# encoding: utf-8
# See http://www.python.org/dev/peps/pep-0263/    

import re
import urllib
import string
from ftplib import FTP
from BeautifulSoup import BeautifulSoup
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from projects.represent.models import Story, Official, Office, Post, Borough
from projects.represent.geocode import geocode_address, google_geocode
from django.contrib.gis.geos import *
from django.core.cache import cache

def urlize_address(address):
    return re.sub("\W+", '-', re.sub('-', '_', address))

def deurlize_address(address):
    return re.sub('_', '-', re.sub('-', ' ', address))

## Session

def find_reps(location, apikey):
    '''Given a location string, returns a normalized address and a list of representatives.'''
    
    # The cache has two kinds of entries: 
    # Non-normalized addresses map into the normalized version. 
    # Normalized addresses map into the data
    
    print "Looking up reps for %s" % (location)
    
    # Try to get the representatives from the cache
    cache_data = cache.get(location)

    if cache_data and isinstance(cache_data, unicode):
        location = cache_data
        print "Got normalized location from cache"
        cache_data = cache.get(location)
        
    if cache_data:
        print "Cache hit on '%s'" % (location)
        print cache_data
        geocoder_results, district_ids, official_ids = cache_data
        districts = Office.objects.filter(id__in=district_ids)
        officials = Official.objects.filter(id__in=official_ids)
        normalized_location = geocoder_results[0][:-5]
        pnt = Point(geocoder_results[1])
    else:
        print "Cache miss on '%s'" % (location)
        
        geocoder_results = google_geocode(location, apikey)
        pnt = Point(geocoder_results[1])
        normalized_location = geocoder_results[0][:-5]
#        geocoder_results = geocode_address(location)
#        pnt  = Point(float(geocoder_results['long']), float(geocoder_results['lat']))
#        normalized_location = "%s %s %s %s" % (geocoder_results['address'], geocoder_results['city'], geocoder_results['state'], geocoder_results['zip'][0:5])
        
        # Searches for districts within 50 ft of the given point - to deal with boundary addresses
        districts = Office.objects.filter(poly__contains=pnt).order_by('sort', 'district')
        #districts = Office.objects.filter(poly__dwithin=(pnt, 0.00011200)).order_by('sort', 'district')
        
        officials = []
        for district in districts:
            for official in district.official_set.filter(is_active=True):
                officials.append(official)
    
        # Add Senators
        senators = Official.objects.filter(office__name='U.S. Senate', is_active=True)
        officials += list(senators)
    
        # Add borough president
        borough = __borough(geocoder_results[2])
        presidents = Official.objects.filter(office__name='Borough President', office__description=borough, is_active=True)
        officials = list(presidents) + officials
        
        # Cache the result
        district_ids = map(lambda d: d.id, districts)
        official_ids = map(lambda o: o.id, officials)
        cache_data = (geocoder_results, district_ids, official_ids)
        print "Caching: '%s'" % normalized_location
        cache.set(normalized_location, cache_data)
#        if normalized_location != location:
#            print "Adding cache entry %s -> %s" % (location, normalized_location)
#            cache.set(location, normalized_location)
        
    return normalized_location, districts, officials, pnt

def __borough(zip_code):
    '''Returns the borough of a zip code'''
    # Manhattan, Queens, Brooklyn, Staten Island, The Bronx
    zip_code_prefix_map = {'100': 'Manhattan', '101': 'Manhattan', '103': 'Staten Island', '104': 'The Bronx', '112': 'Brooklyn', '111': 'Queens', '113': 'Queens', '114': 'Queens', '116': 'Queens'}        
    if zip_code[0:3] in zip_code_prefix_map:
        return zip_code_prefix_map[zip_code[0:3]]


