import re, sys
from django.shortcuts import render_to_response, get_object_or_404
from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpRequest, HttpResponseNotFound, HttpResponseBadRequest
from projects.represent.models import Office, Official, Story, BlogrunnerItem, Post, Source
from djangodblog.models import ErrorBatch, Error
from projects.represent.utils import *
from django.contrib.gis.maps.google import GoogleMap
from django.contrib.gis.utils import GeoIP
from django.template.loader import render_to_string
import datetime
import urllib2
from projects.geocoders.google import GeocodeError
from projects.represent.activity import *

api_key_dict = {}

def index(request):

    feedback_url = "mailto:represent@nytimes.com?subject=Feedback%20for%20" + urllib2.quote(request.path)

    # Redirect represent?location=address to results page represent/address
    if request.GET.has_key('location') and len(request.GET['location']) > 0:
        location = request.GET['location']
        return login(request, location)

    # Redirect logged in users to results page
    if request.session.has_key('location'):
        url = urlize_address(request.session['location'])
        return HttpResponseRedirect(url)

    return render_to_response('index.html', {'feedback_url': feedback_url })

def login(request, location):
    print "Logging in at %s" % location
    feedback_url = "mailto:represent@nytimes.com?subject=Feedback%20for%20" + urllib2.quote(request.path)
    # Try to log in
    #location = deurlize_address(location)

    try:
        request.session['location'], x, y, z = find_reps(location, api_key_dict[request.get_host()])
    except GeocodeError, e:
        print "Error: ", sys.exc_type, sys.exc_value
        Error.objects.create(class_name='404', message = "Could not parse address %s" % sys.exc_value, traceback = str(e), datetime=datetime.datetime.now(), url = request.path, server_name=request.META['SERVER_NAME'])
        request.session.flush()
        return HttpResponseNotFound(render_to_string('index.html', {'error': 'I don\'t understand that address.', 'feedback_url':feedback_url}))
    except Exception, e:
        print "Error: ", sys.exc_type, sys.exc_value
        Error.objects.create(class_name='500', message = "Unexpected error %s, %s" % (sys.exc_type, sys.exc_value), traceback = str(e), datetime=datetime.datetime.now(), url = request.path, server_name=request.META['SERVER_NAME'])
#        request.session.flush()
        return HttpResponseNotFound(render_to_string('index.html', {'error': "Something has gone terribly wrong. I'm so sorry.", 'feedback_url': feedback_url}))

    url = "/represent/" + urlize_address(request.session['location'])
    return HttpResponseRedirect(url)

def logout(request):
    if 'location' in request.session:
        del request.session['location']
        request.session.flush()
    return HttpResponseRedirect('/represent/')

def activityfeed(request, location):
    location, districts, officials, best = find_reps(location, api_key_dict[request.get_host()])

    events = create_events(officials)
    boldify_events(events)
    dates = filter_events(cluster_by_date(events)).items()
    dates.sort()
    dates.reverse()
    dates = filter(lambda (date, events): events, dates) # Removes empty dates
    dates = dates[0:18]

    boundary = len(districts) > 5
    feedback_url = "mailto:represent@nytimes.com?subject=Feedback%20for%20" + urllib2.quote(request.path)

    community_boards = []
    # TODO: clean this up
    for district in districts:
       if district.name.startswith("Community Board"):
            community_boards.append(district)

    return render_to_response('activity_feed.html', { 'dates': dates, 'location_url': urlize_address(location), 'location': location, 'best': best, 'map_districts': districts, 'community_boards': community_boards, 'boundary': boundary, 'tab': 'activityfeed' })

def results(request, location):
    print "Getting results"
    # If we're not logged in at location, log in
    if ((not request.session.has_key('location')) or location != urlize_address(request.session['location'])):
        return login(request, location)
    location = request.session['location']

    # Get it from the session
    try:
        location, districts, officials, best = find_reps(location, api_key_dict[request.get_host()])
    except Exception, e:
        print "Error %s" % str(e)
        Error.objects.create(class_name='500', message = 'Server error', traceback = str(e), datetime=datetime.datetime.now(), url = request.path, server_name=request.META['SERVER_NAME'])
        request.session.flush()
        return HttpResponseNotFound(render_to_string('index.html', {'error': 'Please try again.'}))

    boundary = len(districts) > 5
    feedback_url = "mailto:represent@nytimes.com?subject=Feedback%20for%20" + urllib2.quote(request.path)

    if request.get_host() in api_key_dict:
        api_key = api_key_dict[request.get_host()]
    else:
        api_key = None

    rss_url = "/represent/" + urlize_address(location) + ".xml"

    community_boards = []
    # TODO: clean this up
    for district in districts:
        if district.name.startswith("Community Board"):
            community_boards.append(district)

    return render_to_response('results.html', { 'officials': officials, 'location_url': urlize_address(location), 'location': location, 'best': best, 'map_districts': districts, 'community_boards': community_boards, 'boundary': boundary, 'feedback_url': feedback_url, 'API_KEY': api_key, 'rss_url': rss_url, 'tab': 'activity' })

def onthefloor(request, location):
    location, districts, officials, best = find_reps(location, api_key_dict[request.get_host()])

    events = create_vote_events(officials)
    events += create_legislative_bill_intro_events(officials)
    events += create_floor_appearance_events(officials)
    boldify_events(events)
    dates = (cluster_by_date(events)).items()
    dates.sort()
    dates.reverse()
    dates = filter(lambda (date, events): events, dates) # Removes empty dates
    dates = dates[0:6] # TODO: Cut by number of items, not just the date

    boundary = len(districts) > 5
    community_boards = []
    # TODO: clean this up
    for district in districts:
        if district.name.startswith("Community Board"):
            community_boards.append(district)

    return render_to_response('activity_feed.html', { 'officials': officials, 'dates': dates, 'location_url': urlize_address(location), 'location': location, 'best': best, 'map_districts': districts, 'community_boards': community_boards, 'boundary': boundary, 'tab': 'onthefloor' })

def aroundtheweb(request, location):
    location, districts, officials, best = find_reps(location, api_key_dict[request.get_host()])

    events = create_blog_runner_events(officials)
    events += create_latest_twitter_events(officials)
    boldify_events(events)
    dates = (cluster_by_date(events)).items()
    dates.sort()
    dates.reverse()
    dates = filter(lambda (date, events): events, dates) # Removes empty dates
    dates = dates[0:8]

    boundary = len(districts) > 5
    feedback_url = "mailto:represent@nytimes.com?subject=Feedback%20for%20" + urllib2.quote(request.path)

    community_boards = []
    # TODO: clean this up
    for district in districts:
        if district.name.startswith("Community Board"):
            community_boards.append(district)

    return render_to_response('activity_feed.html', { 'officials': officials, 'dates': dates, 'location_url': urlize_address(location), 'location': location, 'best': best, 'map_districts': districts, 'community_boards': community_boards, 'boundary': boundary, 'tab': 'aroundtheweb' })

def results_feed(request, location):
    raw_location = location
    try:
        input_location = re.sub('-', ' ', raw_location)
        input_location = re.sub('_', '-', input_location)
        location, districts, officials, best = find_reps(input_location, api_key_dict[request.get_host()])
    except Exception, e:
        Error.objects.create(class_name='500', message = 'Something went wrong', traceback = str(e), datetime=datetime.datetime.now(), url = request.path, server_name=request.META['SERVER_NAME'])
        return HttpResponseNotFound('I don\'t understand that address.')

    # Redirect to the canonical URL for this address
    if raw_location != urlize_address(location):
        url = "/represent/" + urlize_address(location) + '.xml'
        return HttpResponseRedirect(url)

    events = create_events(officials)
    boldify_events(events)
    dates = filter_events(cluster_by_date(events)).items()
    dates.sort()
    dates.reverse()
    dates = filter(lambda (date, events): events, dates) # Removes empty dates
    dates = dates[0:12]

    xml = render_to_string('results_feed.xml', { 'url': re.sub('\.xml$', '', request.build_absolute_uri()), 'officials': officials, 'dates': dates, 'location': location })

    return HttpResponse(xml, mimetype='application/xml')

def district_kml(request, id):
    d = Office.objects.kml().get(id=id)
    kml = render_to_string('district.kml', {'place': d })
    return HttpResponse(kml, mimetype='application/xml')

def gmap(request, id):
    api_key = api_key_dict[request.META['SERVER_NAME']]
    d = Office.objects.filter(id=id)
    return render_to_response('map.html', {'district': d[0], 'google' : GoogleMap(key=api_key)})

def everyblock(request):

    if request.GET.has_key('since') and len(request.GET['since']) > 0:
        since = int(request.GET['since']) # unix timestamp
        start = datetime.datetime.fromtimestamp(since)
    else:
        start = datetime.datetime.today() - datetime.timedelta(hours=24)

    t = start.strftime("%Y-%m-%d %H:%M")
    posts = Post.objects.filter(created__gte=t).select_related().order_by('-created')
    stories = Story.objects.filter(created__gte=t).select_related().order_by('-created')
    events = []

    for post in posts:
        for official in post.officials.all():
            if official.office.name != "U.S. Senate":
                events.append(create_blog_post_event(post, official))

    for story in stories:
        for official in story.officials.all():
            if official.office.name != "U.S. Senate":
                events.append(create_article_event(story, official))

    events.sort(key=lambda e:e.created)
    return render_to_response('everyblock.atom', { 'events': events, 'now': datetime.datetime.today() }, mimetype='application/atom+xml')

def fortgreene(request):
    # TODO: dedupe, etc.
    districts = [ Office.objects.get(name='City Council', district=35), Office.objects.get(name='State Assembly', district=57), Office.objects.get(name='State Assembly', district=50), Office.objects.get(name='State Senate', district=18), Office.objects.get(name='Congress', district=10) ]
    officials = map(lambda d: d.current_official(), districts)
    events = create_events(officials)
    boldify_events(events)
    dates = filter_events(cluster_by_date(events)).items()
    dates.sort()
    dates.reverse()
    dates = filter(lambda (date, events): events, dates) # Removes empty dates
    dates = dates[0:8]
    return render_to_response('fortgreene.html', {'dates': dates })

def admin_overview(request):
    city_council_districts = Office.objects.filter(name='City Council').order_by('district')
    state_assembly_districts = Office.objects.filter(name='State Assembly').order_by('district')
    state_senate_districts = Office.objects.filter(name='State Senate').order_by('district')
    congressional_districts = Office.objects.filter(name='Congress').order_by('district')
    return render_to_response('admin/overview.html', { 'district_collections': {'City Council': city_council_districts, 'State Assembly': state_assembly_districts, 'State Senate': state_senate_districts, 'U.S. Congress': congressional_districts } })
