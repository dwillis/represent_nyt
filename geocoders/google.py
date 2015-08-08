import urllib
from utils import simplejson, partial2

# http://code.google.com/apis/maps/documentation/geocoding/index.html

class GeocodeError(Exception):
    pass

def geocode(q, api_key):
    json = simplejson.load(urllib.urlopen(
        'http://maps.google.com/maps/geo?' + urllib.urlencode({
            'q': q,
            'output': 'json',
            'oe': 'utf8',
            'sensor': 'false',
            'key': api_key
        })
    ))
    if json['Placemark'][0]['AddressDetails']['Accuracy'] > 7 and json['Placemark'][0]['AddressDetails']['Country']['AdministrativeArea']['AdministrativeAreaName'] == 'NY':
        try:
            lon, lat = json['Placemark'][0]['Point']['coordinates'][:2]
            name = json['Placemark'][0]['address']
            try:
                zc = json['Placemark'][0]['AddressDetails']['Country']['AdministrativeArea']['Locality']['PostalCode']['PostalCodeNumber']
            except:
                zc = json['Placemark'][0]['AddressDetails']['Country']['AdministrativeArea']['SubAdministrativeArea']['Locality']['DependentLocality']['PostalCode']['PostalCodeNumber']
            return name, (lon, lat), zc
        except:
            raise GeocodeError("No results from geocoder")
    else:
        raise GeocodeError("No results from geocoder")

geocoder = partial2(geocode)
