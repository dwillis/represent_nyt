# encoding: utf-8
# See http://www.python.org/dev/peps/pep-0263/

## Activity stream

import re
import sys
import shelve
import urllib2
from xml.dom import minidom
import time, datetime
import feedparser
from feedcache import cache
from projects.represent.templatetags.humanize import trim_title
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
import unicodedata

class Event:
    '''An item in an activity feed.'''
    def __init__(self, date, text, thumbnail_url, official, category, url, link_title, created=None):
        self.date = date
        self.text = text
        self.thumbnail_url = thumbnail_url
        self.my_officials = set((official,))
        self.category = category
        self.url = url
        self.link_title = link_title
        self.created = created
        self.bold = False

class Vote:
    def __init__(self):
        pass

class Floor:
    def __init__(self):
        pass

class Bill:
    def __init__(self):
        pass

class Tweet:
    def __init__(self, date, text, url):
        self.date = date
        self.text = text
        self.url = url

## Decorators
# Calls that depend on external services
def service_call(fn):
    # TODO: Add timeout
    return fail_gracefully(fn)

# Calls that should fail gracefully
def fail_gracefully(fn):
    def new(*args):
        try:
            return fn(*args)
        except Exception, ex:
            message = "Caught error in %s: %s (%s)" % (fn.__name__, ex, ex.__class__)
            print(message) # TODO: log this
            msg = EmailMultiAlternatives("Error in Represent", message, settings.SERVER_EMAIL, [a[1] for a in settings.ADMINS])
            msg.send(fail_silently=True)
            return []
    return new

def create_events(officials):
    '''Returns all the events for a list of officials'''
    events = create_article_events(officials)
    events += create_blog_post_events(officials)
    events += create_vote_events(officials, 20) # slow
    events += create_blog_runner_events(officials)
    events += create_floor_appearance_events(officials)
    events += create_legislative_bill_intro_events(officials)
    events += create_latest_twitter_events(officials)
    events.sort(key=lambda e: e.date)
    events.reverse()
    return events

def filter_events(date_map):
    '''Removes less interesting events from the main tab'''
    # Filter items
    for date, events in date_map.items():

        # Remove articles just about a senator
        filtered = []
        for event in events:
            if len(event.my_officials) == 1:
                o = event.my_officials.copy().pop()
                if o.office.name == "U.S. Senate" and (event.category == 'story' or event.category == 'post' or event.category == 'blogrunneritem'):
                    continue
            filtered.append(event)
        events = filtered

        ## Remove votes with low score
        filtered = []
        for event in events:
            if event.category == "vote":
                if event.vote_score <= 0:
                    continue
            filtered.append(event)
        events = filtered

        # Don't repeat the same official or the same topic for floor appearances on the same day
        appeared = []
        filtered = []
        titles = []
        for i in range(0, len(events)):
            if events[i].category == 'appearance':
                if events[i].my_officials not in appeared and events[i].link_title not in titles:
                    filtered.append(events[i])
                appeared.append(events[i].my_officials)
                titles.append(events[i].link_title)
            else:
                filtered.append(events[i])
        events = filtered

        # TODO: Cluster when appropriate
        if len(events) > 0:
            deduped = [events[0]]
            for i in range(1, len(events)):
                # Remove similar stories about the same people in a row, even across days
                if events[i].my_officials == events[i-1].my_officials and events[i].category == events[i-1].category:
                    continue
                deduped.append(events[i])
            events = deduped

        events.sort(key=lambda e: e.date)
        events.reverse()
        date_map[date] = events

    # The Hillary rule: remove consecutive stories about a senator, even across days
    #previous_event = None
    #for date, events in date_map.items():
    #    filtered_events = []
    #    for event in events:
    #        o = event.my_officials.copy().pop()
    #        # For now just remove stories about Hillary. TODO: fix this
    #        if len(event.my_officials) == 1 and o.office.name == "U.S. Senate" and event.category != "vote":
    #            continue
    #        filtered_events.append(event)
    #        previous_event = event
    #    date_map[date] = filtered_events
    return date_map

def cluster_by_date(events):
    '''Returns a hash from date to list of events'''
    date_map = {} # date => events
    for event in events:
        date = event.date
        if date not in date_map:
            date_map[date] = [event]
        else:
            date_map[date].append(event)
    return date_map

def boldify_events(events):
    for event in events:
        event.bold = \
          len(event.my_officials) >= 3 or \
          len(filter(lambda o: o.office.name != "U.S. Senate", event.my_officials)) >= 2 or \
          event.category == "vote" and event.vote_score >= 20


## NYTimes stories

def create_article_events(officials):
    event_map = {} # url -> Event
    for official in officials:
        for story in official.story_set.all().order_by('-date'):
            if story.title == 'CITY ROOM BLOGGING AT NYTIMES.COM/CITYROOM.':
                continue
            if story.url in event_map:
                event_map[story.url].my_officials.add(official)
            else:
                event_map[story.url] = create_article_event(story, official)
    return event_map.values()

def create_article_event(story, official):
    text, date, link_title = __extract_story_details(story)
    event = Event(date, text, story.thumbnail_url, official, 'story', story.url, link_title, story.created)
    return event

def __extract_story_details(story):
    '''Finds the activity feed text and date of a story.'''
    text = None
    title = __repair(story.title)
    # TODO: Handle LETTERS
    match = re.match("(OP\-ED.+;)\ (.*)", title)
    if not text and match:
        text = "appeared in the OP-ED: <span><img class='nytint-icon' src='http://nytimes.com/favicon.ico' alt='The New York Times' /><a href=\"%s\">%s</a></span>" % (story.url, match.groups()[1])
    match = re.match("(EDITORIAL;)\ (.*)", title)
    if not text and match:
        text = "appeared in the editorial: <span><img class='nytint-icon' src='http://nytimes.com/favicon.ico' alt='The New York Times' /><a href=\"%s\">%s</a></span>" % (story.url, match.groups()[1])
    match = re.match("(GUEST COLUMNIST;)\ (.*)", title)
    if not text and match:
        text = "appeared in the column: <span><img class='nytint-icon' src='http://nytimes.com/favicon.ico' alt='The New York Times' /><a href=\"%s\">%s</a></span>" % (story.url, match.groups()[1])
    match = re.match("(.*;)\ (.*)", title)
    if not text and match:
        text = "appeared in the article: <span><img class='nytint-icon' src='http://nytimes.com/favicon.ico' alt='The New York Times' /><a href=\"%s\">%s</a></span>" % (story.url, match.groups()[1])
    if not text:
        text = "appeared in the article: <span><img class='nytint-icon' src='http://nytimes.com/favicon.ico' alt='The New York Times' /><a href=\"%s\">%s</a></span>" % (story.url, title)
    date = story.date
    return text, date, title


## Blog posts

def create_blog_post_events(officials):
    event_map = {} # url -> Event
    for official in officials:
        for post in official.post_set.all().order_by('-date'):
            if post.url in event_map:
                event_map[post.url].my_officials.add(official)
            else:
                event_map[post.url] = create_blog_post_event(post, official)
    return event_map.values()

def create_blog_post_event(post, official):
    date = post.date
    text = "appeared in the City Room post: <span><img class='nytint-icon' src='http://nytimes.com/favicon.ico' alt='Blog post:' /><a href=\"%s\">%s</a></span>" % (post.url, post.title)
    event = Event(date, text, post.thumbnail_url, official, 'post', post.url, post.title, post.created)
    return event


## BlogRunner items

def create_blog_runner_events(officials):
    event_map = {} # url -> Event
    for official in officials:
        for blogrunneritem in official.blogrunneritem_set.filter(source__hidden=False).order_by('-date'):
            if blogrunneritem.url in event_map:
                event_map[blogrunneritem.url].my_officials.add(official)
            else:
                event_map[blogrunneritem.url] = create_blog_runner_event(blogrunneritem, official)
    return event_map.values()

def create_blog_runner_event(blogrunneritem, official):
    text = "appeared in:<br/><span><h6 class='nytint-blogrunner'><a href=\"%s\">%s</a></h6> <a href=\"%s\">%s</a></span>" % (blogrunneritem.url, blogrunneritem.source, blogrunneritem.url, blogrunneritem.title)
    event = Event(blogrunneritem.date, text, None, official, 'blogrunneritem', blogrunneritem.url, blogrunneritem.title, blogrunneritem.created)
    return event


def __repair(s):
    """Repairs strings where multibyte characters have been split"""
    return s.replace(u'Ã©', u'é').replace(u'Ã¨', u'è')

## Congressional floor appearances

def create_floor_appearance_events(officials):
    event_map = {}
    for official in officials:
        if not official.congress_id:
            continue
        recent_appearances = latest_congressional_floor_activity(official.congress_id)
        if recent_appearances:
            for appearance in recent_appearances:
                year, month, day = time.strptime(appearance.date, "%Y-%m-%d")[0:3]
                date = datetime.date(year, month, day)
                text = "spoke on the floor of the %s about:<br/> <a href=\"%s\">%s</a>" % (official.office.get_body(), appearance.url, appearance.title)
                if text in event_map:
                    event_map[text].my_officials.add(official)
                else:
                    event = Event(date, text.strip, None, official, 'appearance', appearance.url, appearance.title)
                    event_map[text] = event
    return event_map.values()

@fail_gracefully
def create_vote_events(officials, threshold=None):
    event_map = {}
    for official in officials:
        if not official.congress_id:
            continue
        recent_votes = latest_congress_votes(official.congress_id)
        if recent_votes:
            for vote in recent_votes:
                score = score_vote(vote)
                if threshold and score < threshold:
                    continue
                if not vote.billtitle:
                    continue
                year, month, day = time.strptime(vote.date, "%Y-%m-%d")[0:3]
                date = datetime.date(year, month, day)
                if vote.billquestion.strip() == 'On Passage' or vote.billquestion.strip() == 'On the Nomination' or vote.billquestion.strip() == 'On the Conference Report' or vote.billquestion.strip() == 'On Agreeing to the Conference Report':
                    bill_title = vote.billtitle.strip()
                else:
                    bill_title = vote.billtitle.strip() + ': '+ vote.billquestion.strip()
                vote_url = "http://politics.nytimes.com/congress/votes/%s/%s/%s/%s" % (vote.congressnumber, vote.chamber.lower(), vote.sessionnumber, vote.roll)
                # TODO: Trim titles like: S. 386 as Amended; FERA: On Passage of the Bill
                action = vote.member_position.lower()
                if action == "not voting":
                    action_text = "missed a vote on"
                else:
                    action_text = "voted <b>%s</b> on" % (action)
                text = "%s: <span><a href=\"%s\">%s</a></span>" % (action_text, re.sub('&', '&amp;', vote_url), bill_title)
                if text in event_map:
                    event_map[text].my_officials.add(official)
                else:
                    event = Event(date, text.strip, None, official, 'vote', vote_url, bill_title)
                    event.vote_score = score
                    event.vote = vote
                    event_map[text] = event
    return event_map.values()

@fail_gracefully
def create_legislative_bill_intro_events(officials, threshold=None):
    event_map = {}
    for official in officials:
        if not official.office.name[0:5] == u'State':
            continue
        recent_intros = latest_legislature_bills(official.slug)
        if recent_intros:
            for bill in recent_intros:
                year, month, day = time.strptime(bill.introduced_date, "%Y-%m-%d")[0:3]
                date = datetime.date(year, month, day)
                text = "introduced a bill:<br /><a href=\"%s\">%s</a>" % (bill.url, trim_title(bill.title))
                if text in event_map:
                    event_map[text].my_officials.add(official)
                else:
                    event = Event(date, text.strip, None, official, 'bill', bill.url, bill.title)
                    event_map[text] = event
    return event_map.values()

@service_call
def latest_legislature_bills(member_slug):
    url = "http://projects.nytimes.com/nylegis/svc/politics/v2/ny/legislative/members/%s/bills/introduced" % member_slug
    output = []
    f = urllib2.urlopen(url)
    html = f.read()
    f.close()
    xml = minidom.parseString(html)
    for bill in xml.getElementsByTagName('bill'):
        d = {}
        b = Bill()
        for var in ('number', 'title', 'introduced_date', 'url'):
            if bill.getElementsByTagName(var)[0].firstChild:
                d[var.lower()] = bill.getElementsByTagName(var)[0].firstChild.nodeValue
                setattr(b, var.lower(), bill.getElementsByTagName(var)[0].firstChild.nodeValue)
            else:
                d[var.lower()] = u''
                setattr(b, var.lower(), None)
        output.append(b)
    return output

@fail_gracefully
def create_latest_twitter_events(officials, threshold=None):
    event_map = {}
    for official in officials:
        if not official.twitter_rss_url:
            continue
        recent_tweets = latest_tweets(official.twitter_rss_url)
        if recent_tweets:
            for tweet in recent_tweets:
                text = "posted on Twitter:<br/> <a href=\"%s\">%s</a>" % (tweet.url, tweet.text)
                if text in event_map:
                    event_map[text].my_officials.add(official)
                else:
                    event = Event(tweet.date, text, None, official, 'tweet', tweet.url, 'tweeted')
                    event_map[text] = event
    return event_map.values()


@service_call
def latest_tweets(twitter_url):
    output = []
    try:
        storage = shelve.open('/var/tmp/.feedcache')
        c = cache.Cache(storage)
        f = c.fetch(twitter_url)
    except:
        f = feedparser.parse(twitter_url)
    for entry in f.entries:
        t = Tweet(date = datetime.date(entry.updated_parsed[0],entry.updated_parsed[1], entry.updated_parsed[2]), url = entry.link, text = entry.title.split(":", 1)[1])
        output.append(t)
    return output

@service_call
def latest_congressional_floor_activity(member_id):
    '''Gets the latest floor appearances of a member of Congress from CSPAN's Congressional Chronicle app.
       Unlike stories and blog posts, votes are fetched at runtime.'''
    url = "http://api.nytimes.com/svc/politics/v2/us/legislative/congress/members/%s/floor_appearances" % member_id
    output = []
    f = urllib2.urlopen(url)
    html = f.read()
    f.close()
    xml = minidom.parseString(html)
    for appearance in xml.getElementsByTagName('appearance'):
        d = {}
        a = Floor()
        for var in ('date', 'title', 'url', 'start_time', 'end_time'):
            if appearance.getElementsByTagName(var)[0].firstChild:
                d[var.lower()] = appearance.getElementsByTagName(var)[0].firstChild.nodeValue
                setattr(a, var.lower(), appearance.getElementsByTagName(var)[0].firstChild.nodeValue)
            else:
                d[var.lower()] = u''
                setattr(a, var.lower(), None)
        output.append(a)
    return output

@service_call
def latest_congress_votes(member_id):
    '''Gets the latest votes of a member of congress from the Congressional Votes application.
       Unlike stories and blog posts, votes are fetched at runtime.'''
    outcomes = {'Cloture on the Motion to Proceed Agreed to': 1, 'Motion to Proceed Agreed to': 1, 'Motion Agreed to': 1, 'Passed': 1, 'Joint Resolution Passed':1, 'Agreed to': 1, 'Confirmed': 1, 'Nomination Confirmed': 1, 'Bill Passed': 1,
                'Amendment Agreed to': 1, 'Cloture Motion Agreed to': 1, 'Conference Report Agreed to': 1, 'Motion to Table Agreed to': 1, 'Held Germane': 1,
                'Guilty': 1, 'Not Guilty': 0, 'Sustained': 1, 'Point of Order Sustained': 1, 'Veto Overridden': 1, 'Pelosi': 1, 'Boehner':0, 'Rejected': 0,
                'Held Nongermane': 0, 'Not Sustained': 0, 'Failed': 0, 'Veto Sustained': 0, 'Not Well Taken': 0, 'Motion Rejected': 0, 'Motion to Recommit Rejected': 0,
                'Amendment Rejected': 0, 'Nomination Rejected': 0, 'Conference Report Rejected': 0, 'Cloture Motion Rejected': 0, 'Point of Order Not Sustained': 0, 'Point of Order Not Well Taken':0}

    url = "http://politics.nytimes.com/congress/external/member_recent_votes/%s" % member_id
    f = urllib2.urlopen(url)
    html = f.read()
    f.close()
    xml = minidom.parseString(html)
    output = []
    for vote in xml.getElementsByTagName('vote'):
        d = {}
        v = Vote()
        for var in ('roll', 'date', 'billnumber', 'billquestion', 'voteresult', 'billtitle', 'yesvotes', 'novotes', 'notvoting', 'member_position', 'chamber', 'congressnumber', 'sessionnumber' ):
            if vote.getElementsByTagName(var)[0].firstChild:
                d[var.lower()] = vote.getElementsByTagName(var)[0].firstChild.nodeValue
                setattr(v, var.lower(), vote.getElementsByTagName(var)[0].firstChild.nodeValue)
            else:
                d[var.lower()] = u''
                setattr(v, var.lower(), None)
            if var.lower() == 'voteresult' and outcomes[vote.getElementsByTagName(var)[0].firstChild.nodeValue] == 1:
                setattr(v, 'is_passed', 1)
            elif var.lower() == 'voteresult' and outcomes[vote.getElementsByTagName(var)[0].firstChild.nodeValue] == 0:
                setattr(v, 'is_passed', 0)
            elif var.lower() == 'voteresult':
                continue
        output.append(v)
    return output

def score_vote(vote):
    '''Figure out if a congressional vote belongs on the main tab'''
    score = 0

    # Close votes
    if abs(int(vote.yesvotes) - int(vote.novotes)) < 30:
        score += 1

    # Type of question
    if 'passage' in vote.billquestion.lower():
        score += 20
    if 'conference report' in vote.billquestion.lower():
        score += 20
    if 'cloture' in vote.billquestion.lower():
        score += 5
    if 'nomination' in vote.billquestion.lower():
        score += 10

    # Rules
    if 'suspend the rules' in vote.billquestion.lower():
        score -= 5

    return score
