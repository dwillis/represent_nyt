"""
Functions for importing stories and blog posts into the database.
These are for use from the console or in cron scripts, but not from the web app.

For example,
$ python manage.py shell
>>> import projects.represent.dataimport as dataimport
>>> dataimport.fetch_stories_for_all()
>>> dataimport.import_cityroom_posts()
>>> dataimport.import_blogrunner_items()

>>> reload(dataimport)
"""
import re
import urllib
import time, datetime
import feedparser
from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup
from projects.represent.models import Story, Official, Office, Post, BlogrunnerItem, Source
from django.conf import settings
from django.core.mail import EmailMultiAlternatives

# not currently used.
def import_floor_appearances():
    '''Gets the latest floor appearances of a member of Congress from CSPAN's Congressional Chronicle app.'''
    officials = Official.objects.filter(is_active=True, office__level = 'F')
    for official in officials:
        try:
            url = "http://www.c-spanarchives.org/congress/feed.php?type=person&id=%s" % official.cspan_id
            f = feedparser.parse(url)
        except e:
            subject = "Error on congressional floor activity for %s" % member_id
            message = e
            msg = EmailMultiAlternatives(subject, message, settings.SERVER_EMAIL, [a[1] for a in settings.ADMINS])
            msg.send(fail_silently=True)
        if f:
            for entry in f.entries:
                date = datetime.date(entry.updated_parsed[0], entry.updated_parsed[1], entry.updated_parsed[2])
                url = entry.link
                title = entry.title.title()
                splits = entry.description.split(' ')
                st = time.strptime(splits[0]+' '+splits[1], '%Y-%m-%d %H:%M:%S')
                et = time.strptime(splits[0]+' '+splits[3], '%Y-%m-%d %H:%M:%S')
                fa, created = FloorAppearance.objects.get_or_create(official=official, date=date, url=url, title=title, start_time=datetime.datetime(*st[:6]), end_time=datetime.datetime(*et[:6]))
                if created:
                    html = urllib.urlopen(fa.url).read()
                    soup = BeautifulSoup(html)
                    if soup.iframe and soup.iframe['src']:
                        fa.embed_code = soup.iframe['src']
                        h2 = urllib.urlopen(soup.iframe['src']).read()
                        s2 = BeautifulSoup(h2)
                        if s2.img['src']:
                            fa.image_url = 'http://www.c-spanarchives.org'+str(s2.img['src'])
                            fa.save()
                        else:
                            pass
                    else:
                        pass

def import_blogrunner_items():
    officials = Official.objects.filter(is_active=True)
    black_list = ["New York Times",'City Room','us.rd.yahoo.com'] # list of sources we don't want to add via blogrunner
    for official in officials:
        if official.has_times_topic_url():
            xml = urllib.urlopen(official.blogrunner_rss_url()).read()
            soup = BeautifulStoneSoup(xml)
            for entry in soup.findAll('item'):
                if entry.source.contents[0] not in black_list:
                    source, created = Source.objects.get_or_create(name=str(entry.source.contents[0]))
                    url = str(entry.link.contents[0])
                    dt = time.strptime(entry.pubdate.contents[0], "%a, %d %b %Y %H:%M:%S %Z")
                    date = datetime.date(dt[0], dt[1], dt[2])
                    item, created = BlogrunnerItem.objects.get_or_create(url=url, date=date, source=source)
                    item.title = str(entry.title.contents[0])
                    item.text = str(entry.description.contents[0])
                    item.save()
                    if official not in item.officials.all():
                        item.officials.add(official)
        else:
            pass


def import_cityroom_posts():
    feed = feedparser.parse("http://cityroom.blogs.nytimes.com/rss2-full.xml")
    new_posts, old_posts, new_associations = 0, 0, 0
    for entry in feed.entries:
        date = datetime.date(entry.updated_parsed[0], entry.updated_parsed[1], entry.updated_parsed[2])
        post, created = Post.objects.get_or_create(url=entry.link, date=date)
        post.title=entry.title
        post.text=entry.full_text
        post.excerpt=entry.excerpt
        post.save()
        officials = Official.objects.filter(is_active=True)
        for official in officials:
            name = official.display_name()
            queries = generate_variants(name)
            for query in queries:
                if query.replace('"','') in post.text and official not in post.officials.all():
                    post.officials.add(official)
                    new_associations += 1
                if created:
                    new_posts += 1
                else:
                    old_posts += 1

    print "Imported %d new posts" % new_posts
    print "Added %d new associations" % new_associations
    print "Already had %d posts" % old_posts

def fetch_stories_for(official_id, verbose=False):
    '''Adds stories about a representative to the story table.'''
    official = Official.objects.get(id=official_id)
    if not official:
        raise "No official with id = %s" % official_id
    name = official.display_name().strip()
    queries = generate_variants(name)

    # Compile regular expressions
    date_in_description = re.compile('.*([A-Z][a-z]+ [0-9][0-9]?, [0-9]{4}).*', re.MULTILINE + re.DOTALL)

    print "%s (id=%d)" % (name, official_id)
    for query in queries:
        print ("\tquery = %s" % query).ljust(40),
        params = urllib.urlencode({ 'partner': 'MICROSOFT', 'query': query })
        url = 'http://query.nytimes.com/search_service/query?%s' % params
        if verbose:
            print "Requesting URL: ", url
        result = feedparser.parse(url)
        print "%4d" % len(result.entries),
        new_stories, skipped_stories, old_stories, new_associations = 0, [], 0, 0
        for entry in result.entries:
            year, month, day = extract_date_from_url(entry.link)
            if not year:
                # Try to parse date from story description
                match = date_in_description.match(entry.description)
                if match:
                    date_string = match.groups()[0].replace("Sept\.", "September")
                    try:
                        year, month, day = time.strptime(date_string, "%B %d, %Y")[0:3]
                    except ValueError:
                        pass
            if not year:
                if verbose:
                    print "Could not find date on: ", entry.link
                skipped_stories.append(entry.link)
                continue
            published = datetime.date(year, month, day)

            # Remove extraneaous get parameters from the article URL.
            # We can remove all of them, except for URLs that look like
            # http://query.nytimes.com/gst/fullpage.html?res=..., in which case we
            # just remove the trailing Microsoft partner parameters.
            match = re.match("(http://query.nytimes.com/gst/fullpage.html\?res=[A-Z0-9]+)(\&vendor=MICROSOFT\&partner=MICROSOFT)", entry.link)
            if match:
                link, msft_params = match.groups()
                entry.link = link
            else:
                match = re.match('(.*)\?(.*)', entry.link).groups()
                link, params = match[0], match[1]
                if params:
                    entry.link = link

            title = repair_mojibake(entry.title)
            story, created = Story.objects.get_or_create(url=entry.link, date=published)
            if created:
                story.title=title
                story.save()

            # check for thumbnail image and add if exists
            match = re.search("(http://graphics8.nytimes.com/.*jpg)", entry.summary)
            if match:
                story.thumbnail_url = match.groups()[0]
                story.save()

            # Add associations
            if official not in story.officials.all():
                story.officials.add(official)
                new_associations += 1
            if created:
                new_stories += 1
            else:
                old_stories += 1
        print "%4d %4d %4d" % (new_stories, old_stories, new_associations)
    if len(skipped_stories) > 0:
        print "ERROR: Could not parse %d stories:\n   %s" % (len(skipped_stories), "\n   ".join(skipped_stories))
    return new_stories

def delete_all_stories():
    Story.objects.all().delete()

def delete_stories_for(official_id):
    Official.objects.get(id=official_id).story_set.all().delete()

def fetch_stories_for_all():
    total = 0
    for official in Official.objects.filter(is_active=True):
        total += fetch_stories_for(official.id)
    print "\n\n=== Done. Got %d new stories. ===\n" % total

def update():
    fetch_stories_for_all()
    import_cityroom_posts()
    import_blogrunner_items()

# ---

repair_table = ((u'\342\200\231', "'"),
                (u'\342\200\230', "'"),
                (u'\342\200\232', "'"))

def repair_mojibake(string):
    '''Repairs mojibaked characters.'''
    return reduce(lambda s, p: s.replace(p[0], p[1]), repair_table, string)

def generate_variants(name):
    '''Returns an array of variants of a name'''
    # TODO: Check if query expansion is necessary and avoids false positives
    # TODO: Try to include title in query
    queries = ['"%s"' % name]
    # Try removing middle initial
    toks = name.split(' ')
    if len(toks) == 3:
        (first, middle, last) = toks
        if middle != 'de' and last not in ('Jr.', 'Sr.', 'III', 'IV'):
            query = '"%s %s"' % (first, last)
            queries.append(query)
    return queries

# Matches a date in an nytimes article or blog URL
date_in_url = re.compile('(\d{4})/(\d{2})/(\d{2})')

def extract_date_from_url(url):
    '''Tries to get a date from an nytimes URL. Returns a triple of ints or Nones.'''
    match = date_in_url.search(url)
    if match:
        return map(lambda(s): int(s), match.groups())
    else:
        return None, None, None

# ship map files to graphics8. should only be run from jeffvader
# after completed, will need to bust cache on graphics8
def update_kml():
    offices = Office.objects.exclude(name='U.S. Senate').exclude(name='Borough President')
    ftp = FTP('##########', '####', '#####')
    ftp.cwd('/data/publish/packages/xml/represent')
    for office in offices:
        file_name = "%s.xml" % office.id
        url = "http://localhost/represent/office/%s/district.kml" % office.id
        ftp.storlines("STOR " + file_name, urllib.urlopen(url))
