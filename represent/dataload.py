import urllib
import re
import string
import time, datetime
from BeautifulSoup import BeautifulSoup
from projects.represent.models import Story, Official, Office, Post, BlogrunnerItem
from django.contrib.gis.utils import LayerMapping
from django.contrib.gis.gdal import DataSource


def assembly_committee_assignments():
    '''Gets committee assignments for all active State Assembly members.'''
    members = Official.objects.filter(office__name='State Assembly', is_active=True)
    comm_url = 'http://assembly.state.ny.us/mem/?sh=com&ad='
    
    for member in members:
        html = urllib.urlopen(comm_url+str(member.office.district).zfill(3)).read()
        soup = BeautifulSoup(html)
        chair = soup.findAll(text=re.compile('Chair, Committee.*'))
        comm_list = [c.split('Committee on ')[1] for c in soup.findAll(text=re.compile('Member, Committee.*'))]
        if chair:
            ch = chair[0].split('Committee on ')[1] + ' (Chair); '
            c = ch + string.join(comm_list, '; ')
        else:
            c = string.join(comm_list, '; ')
        changed = []
        if member.details == c:
            pass
        else:
            member.details = c
            member.save()
            changed.append(member.display_name)
    if changed:
        print "Updated committee assignments for %s" % [n for n in changed]
    else:
        print "No changes made"

def update_officials(end, start):
    '''Deactivates officials and activates new ones based on end year and start year.
       Usage: update_officials(2008, 2009)
    '''
    ending_members = Official.objects.filter(end_year=end)
    for member in ending_members:
        member.is_active = False
        member.save()
    starting_members = Official.objects.filter(start_year=start)
    for member in starting_members:
        member.is_active = True
        member.save()


# Mapping

def add_city_council_map():
    ds = DataSource('maps/nycc_07cav/nycc.shp')
    
    mapping = { 'district' : 'CounDist',
               'poly' : 'MULTIPOLYGON',
              }
    lm = LayerMapping(Office, ds, mapping)
    lm.save(verbose=True)

def add_assembly_map():
    ds = DataSource('maps/nyad_07cav/nyad.shp')
    
    mapping = {'district' : 'AssemDist',
               'poly' : 'MULTIPOLYGON',
              }
    lm = LayerMapping(Office, ds, mapping)
    lm.save(verbose=True)

def add_senate_map():
    ds = DataSource('maps/nyss_07cav/nyss.shp')
    
    mapping = {'district' : 'StSenDist',
               'poly' : 'MULTIPOLYGON',
              }
    lm = LayerMapping(Office, ds, mapping)
    lm.save(verbose=True)

def add_congressional_map():
    ds = DataSource('maps/nycg_07cav/nycg.shp')
    
    mapping = {'district' : 'CongDist',
               'poly' : 'MULTIPOLYGON',
              }
    lm = LayerMapping(Office, ds, mapping)
    lm.save(verbose=True)


def add_community_district_map():
    ds = DataSource('maps/nycd_08bav/nycd.shp')
    
    mapping = {'district' : 'BoroCD', 'poly' : 'MULTIPOLYGON'}
    lm = LayerMapping(Office, ds, mapping)
    lm.save(verbose=True)