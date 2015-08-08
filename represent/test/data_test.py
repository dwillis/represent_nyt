import urllib, urllib2
from projects.represent.models import Office, Official
from projects.represent.geocode import geocode_address
import csv

def test_addresses():
    from projects.represent.test.data_test import city_council_address_check as checker
    reader = csv.reader(open('represent/test/nyc_addy.csv', 'U'))
    matches = 0
    errors = 0
    bad = 0
    wrong = 0
    err_list = []
    bad_addys = []
    wrong_list = []
    for row in reader:
        r = checker(row[0], row[1], row[2])
        if r == 'match':
            matches += 1
        elif r == 'error':
            errors +=1
            err_list.append(row[0])
        elif r == 'bad_addy':
            bad += 1
            bad_addys.append(row[0])
        elif r == 'wrong member':
            wrong += 1
            wrong_list.append(row[0])
    print "Matched %s records, wrong council member on %s records, bad addresses on %s records, geocoder errors on %s records" % (matches, wrong, bad, errors)
    return err_list, bad_addys, wrong_list

def city_council_address_check(address, borough, zip=''):
    '''Rudimentary utility to compare the results of the NYC council find-your-member lookup and NYT geocoder.
       Street address, borough are required, zip is optional.
       Usage:
       >>> from projects.represent.test.data_test import city_council_address_check as checker
       >>> checker('73 Washington St', 'Brooklyn')
       >>> checker('620 8th Ave', 'Manhattan', '10018')
    '''
    if borough == None:
        print "Must supply a borough name"
        raise
    boroughs = {'Manhattan': 1, 'Bronx': 2, 'Brooklyn': 3, 'Queens': 4, 'Staten Island': 5}
    params = { 'lookup_borough' : boroughs[borough.title()], 'lookup_address': address}
    base_url = 'http://www.nyccouncil.info/includes/scripts/action_lookup.asp?%s' % urllib.urlencode(params)
    request = urllib2.Request(base_url)
    opener = urllib2.build_opener()
    f = opener.open(request)
    try:
        member = Official.objects.get(official_url = f.url)
    except:
        result = 'bad_addy'
        member = None
    
    if member:
        borough = 'New York, NY'
        location = (address + ' '+ borough + ' '+ zip)
        try:
            best = geocode_address(location)
        except:
            result = "error"
        
        try:
            pnt = "POINT(%.5f %.5f)" % (float(best['long']), float(best['lat']))
            district = Office.objects.get(poly__contains=pnt, name='City Council')
            member_nyt = district.official_set.get(is_active=True)
            if member_nyt == member:
                result = "match"
            else:
                result = "wrong member"
        except:
            print "NYT geocoder failed to find council member; City utility found %s" % member.display_name()
            result = 'bad_addy'
            
    return result

# used to check whether an official with a times topic url has a blogrunner feed
# returns a list of officials who don't.
def check_blogrunner_feeds():
    no_feed = []
    officials = Official.objects.filter(is_active=True)
    for official in officials:
        if official.has_times_topic_url():
            req = urllib2.Request(official.blogrunner_rss_url())
            try:
                response = urllib2.urlopen(req)
            except:
                no_feed.append(official)
    return no_feed