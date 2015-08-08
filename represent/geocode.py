# The python half of our geocoding machinery
import re, urllib, sys
from xml.dom import minidom
from projects.geocoders.google import geocoder

def google_geocode(address, api_key):
    
    address, city = __preprocess_address(address)
    geocode = geocoder(api_key)
    results = geocode(address)
    if not results:
        raise GeocodeError("No results from geocoder")
    else:
        return results


def geocode_address(address):
    """Submits an address to our geocoding service
    >>> geocode_address("620 8th Avenue, New York, NY")
    {'city': u'New York', 'zip': u'11215', 'long': u'-73.977818', 'state': u'NY', 'address': u'620 8th Ave', 'lat': u'40.667446'}
    """
    print "Geocoding: %s" % address
    address, city = __preprocess_address(address)
    print "Sending: %s" % address
    params = {'location': address}
    url = 'http://ec2-75-101-176-181.compute-1.amazonaws.com/geocode?%s' % urllib.urlencode(params)
    f = urllib.urlopen(url)
    html = f.read()
    f.close()
    try:
        xml = minidom.parseString(html)
    except Exception:
        print "Exception: ", sys.exc_type, sys.exc_value
        raise GeocodeError, "Invalid XML at %s (%s, %s)" % (url, sys.exc_type, sys.exc_value)

    results = xml.getElementsByTagName('result')
    ds = []
    if not results:
        raise GeocodeError("No results from geocoder")
    for result in results:        
        d = {}
        for var in ('lat', 'long', 'street', 'address', 'city', 'state', 'zip'):
            if len(result.getElementsByTagName(var)) > 0 and result.getElementsByTagName(var)[0].firstChild:
                d[var] = result.getElementsByTagName(var)[0].firstChild.nodeValue
            else:
                d[var] = u''
        ds.append(__postprocess_result(d))
    
    # Choose among multiple results
    match_city = lambda result: int(city.lower() == city_name(result['zip']).lower())
    prefer_manhattan = lambda result: -int(result['zip'][0:5])
    
    for f in (match_city, prefer_manhattan):
        if len(ds) == 1:
            return ds[0]
        ds = argmax_list(ds, f)
    return ds[0]

def __preprocess_address(address):
    """Cleans up address string for the geocoder."""
    address = re.sub(r"(\s)+", ' ', address)
    address = re.sub(r" ,", ',', address)
    address = address.strip()
    
    # Remove hypen from Queens addresses
    # TODO: Restore this after geocoding
    match = re.match("^(\d\d-\d\d)(.*)", address)
    if match:
        address = re.sub('-','', match.groups()[0]) + match.groups()[1]
    
    # Support spelled-out ordinal street names
    address = address.lower()
    address = transform_ordinals(address)
    
    # Our geocoder gets confused by any city name that isn't New York, 
    # so we replace it, taking care not to replace street names
    city = "New York"
    city_names = ["Brooklyn", "Queens", "Bronx", "The Bronx", "Manhattan", "Staten Island", "New York"]
    queens_neighborhood_names = ["Arverne", "Astoria Heights", "Astoria", "Auburndale", "Bay Terrace", "Bayside", "Bayswater", "Beechhurst", "Bellaire", "Belle Harbor", "Bellerose", "Blissville", "Breezy Point", "Briarwood", "Broad Channel", "Cambria Heights", "College Point", "Corona", "Ditmars", "Douglaston", "Dutch Kills", "East Elmhurst", "Edgemere", "Electchester", "Elmhurst", "Far Rockaway", "Floral Park", "Flushing", "Forest Hills Gardens", "Forest Hills", "Fresh Meadows", "Fresh Pond", "Glen Oaks", "Glendale", "Hamilton Beach", "Hammels", "Hillcrest", "Hollis Hills", "Hollis", "Holliswood", "Howard Beach", "Howard Park", "Hunters Point", "Jackson Heights", "Jamaica", "Jamaica Estates", "Jamaica Hills", "Kew Gardens Hills", "Kew Gardens", "Laurelton", "LeFrak City", "Linden Hill", "Lindenwood", "Long Island City", "Little Neck", "Malba", "Maspeth", "Meadowmere", "Middle Village", "Murray Hill", "Neponsit", "New Hyde Park", "North Corona", "Oakland Gardens", "Old Howard Beach", "Ozone Park", "Pomonok", "Queens Village", "Queensbridge", "Ramblersville", "Ravenswood", "Rego Park", "Richmond Hill", "Ridgewood", "Rochdale Village", "Rockaway Beach", "Rockaway Park", "Rockwood Park", "Rosedale", "Roxbury", "Saint Albans", "Seaside", "South Jamaica", "South Ozone Park", "Springfield Gardens", "Sunnyside Gardens", "Sunnyside", "Tudor Village", "Utopia", "Whitestone", "Willets Point", "Woodhaven", "Woodside"]
    city_state_zip_regexp = re.compile("(%s),?\s*(ny)?\s*([0-9]{5}((\-)?[0-9]{4})?)?$" % '|'.join(city_names + queens_neighborhood_names), re.IGNORECASE)
    match = city_state_zip_regexp.search(address)
    if match:
        city = match.groups()[0]
        start = match.start()
        street_address = address[0:start].strip()
        city_state_zip = address[start:].strip()
        city_state_zip = city_state_zip.replace(city, 'New York', 1)
        address = "%s %s" % (street_address, city_state_zip)
        print address
            
    # Make sure we have city and state or zip code
    if re.search("New York(,)?(\s)*NY$", address, re.IGNORECASE):
        return address, city
    if re.search("[0-9]{5}(\-[0-9]{4})?", address):
        return address, city
    if re.search("New York$", address, re.IGNORECASE):
        return address + ", NY", city
        
    address += " New York, NY"
    return address, city

def __postprocess_result(geocode_result):
    """Cleans up results from the geocoder."""
    result = geocode_result.copy()
    result['address'] = re.sub('(\s)+', ' ', result['address'])
    
    # The geocoder seems to think hyphenated Queens addresses have hyphens at the end...
    result['address'] = re.sub('([0-9])\- ', r'\1 ', result['address'])
    
    result['city'] = city_name(result['zip'])
    result['state'] = 'NY'
            
    # TODO: add borough name
    
    return result

def city_name(zip):
    """Finds the Post Office city/neighborhood name for a five-digit zip code
    city_name('11231')
    >>> "Brooklyn"
    city_name('11101')
    >>> "Long Island City"
    """
    zip_code_prefix_map = {'100': 'New York', '101': 'New York', '103': 'Staten Island', '104': 'Bronx', '112': 'Brooklyn'}
        
    zip_code_prefix = zip[0:3]
    if zip_code_prefix in zip_code_prefix_map:
        return zip_code_prefix_map[zip_code_prefix]
        
    # Try to get the current, post-1998 post office city name in Queens
    # See http://query.nytimes.com/gst/fullpage.html?res=9507E3DE113DF930A1575BC0A96E958260
    queens_map = {'11106': 'Astoria', '11693': 'Far Rockaway', '11370': 'East Elmhurst', '11355': 'Flushing', '11354': 'Flushing', '11691': 'Far Rockaway', '11416': 'Ozone Park', '11385': 'Ridgewood', '11368': 'Corona', '11369': 'East Elmhurst', '11366': 'Fresh Meadows', '11367': 'Flushing', '11364': 'Oakland Gardens', '11365': 'Fresh Meadows', '11362': 'Little Neck', '11363': 'Little Neck', '11360': 'Bayside', '11361': 'Bayside', '11429': 'Queens Village', '11428': 'Queens Village', '11419': 'South Richmond Hill', '11697': 'Breezy Point', '11421': 'Woodhaven', '11420': 'South Ozone Park', '11417': 'Ozone Park', '11422': 'Rosedale', '11427': 'Queens Village', '11426': 'Bellerose', '11371': 'Flushing', '11692': 'Arverne', '11694': 'Rockaway Park', '11412': 'Saint Albans', '11418': 'Richmond Hill', '11358': 'Flushing', '11414': 'Howard Beach', '11423': 'Hollis', '11415': 'Kew Gardens', '11372': 'Jackson Heights', '11411': 'Cambria Heights', '11359': 'Bayside', '11109': 'Long Island City', '11379': 'Middle Village', '11378': 'Maspeth', '11005': 'Floral Park', '11004': 'Glen Oaks', '11102': 'Astoria', '11103': 'Astoria', '11377': 'Woodside', '11101': 'Long Island City', '11357': 'Whitestone', '11356': 'College Point', '11104': 'Sunnyside', '11105': 'Astoria', '11375': 'Forest Hills', '11374': 'Rego Park', '11432': 'Jamaica', '11433': 'Jamaica', '11430': 'Jamaica', '11435': 'Jamaica', '11436': 'Jamaica', '11373': 'Elmhurst', '11434': 'Jamaica', '11413': 'Springfield Gardens'}
    if zip in queens_map:
        return queens_map[zip]

    # In case that didn't work, fall back to the pre-1998 Queens postal designation
    # 111 were labeled Long Island City; 113 ZIP codes were designated Flushing, 114 were marked Jamaica and 116 as Far Rockaway.
    old_queens_map = {'111': 'Long Island City', '113': 'Flushing', '114': 'Jamaica', '116': 'Far Rockaway'}
    if zip_code_prefix in old_queens_map:
        return old_queens_map[zip_code_prefix]
        
    raise GeocodeError("Unknown zip code: %s" % zip)

def transform_ordinals(s):
    """
    transform_ordinals("first base")
    >>> "1st base"
    transform_ordinals("eighty-ninth street")
    >>> "89th street"
    """
    # Generated with http://nodebox.net/code/index.php/Linguistics
    # ([ (ordinal.ordinal(numeral.spoken_number(n)), ordinal.ordinal(n))  for n in range(200, 1, -1) ])
    map = [('two hundredth', '200th'), ('one hundred and ninety-ninth', '199th'), ('one hundred and ninety-eighth', '198th'), ('one hundred and ninety-seventh', '197th'), ('one hundred and ninety-sixth', '196th'), ('one hundred and ninety-fifth', '195th'), ('one hundred and ninety-fourth', '194th'), ('one hundred and ninety-third', '193rd'), ('one hundred and ninety-second', '192nd'), ('one hundred and ninety-first', '191st'), ('one hundred and ninetieth', '190th'), ('one hundred and eighty-ninth', '189th'), ('one hundred and eighty-eighth', '188th'), ('one hundred and eighty-seventh', '187th'), ('one hundred and eighty-sixth', '186th'), ('one hundred and eighty-fifth', '185th'), ('one hundred and eighty-fourth', '184th'), ('one hundred and eighty-third', '183rd'), ('one hundred and eighty-second', '182nd'), ('one hundred and eighty-first', '181st'), ('one hundred and eightieth', '180th'), ('one hundred and seventy-ninth', '179th'), ('one hundred and seventy-eighth', '178th'), ('one hundred and seventy-seventh', '177th'), ('one hundred and seventy-sixth', '176th'), ('one hundred and seventy-fifth', '175th'), ('one hundred and seventy-fourth', '174th'), ('one hundred and seventy-third', '173rd'), ('one hundred and seventy-second', '172nd'), ('one hundred and seventy-first', '171st'), ('one hundred and seventieth', '170th'), ('one hundred and sixty-ninth', '169th'), ('one hundred and sixty-eighth', '168th'), ('one hundred and sixty-seventh', '167th'), ('one hundred and sixty-sixth', '166th'), ('one hundred and sixty-fifth', '165th'), ('one hundred and sixty-fourth', '164th'), ('one hundred and sixty-third', '163rd'), ('one hundred and sixty-second', '162nd'), ('one hundred and sixty-first', '161st'), ('one hundred and sixtieth', '160th'), ('one hundred and fifty-ninth', '159th'), ('one hundred and fifty-eighth', '158th'), ('one hundred and fifty-seventh', '157th'), ('one hundred and fifty-sixth', '156th'), ('one hundred and fifty-fifth', '155th'), ('one hundred and fifty-fourth', '154th'), ('one hundred and fifty-third', '153rd'), ('one hundred and fifty-second', '152nd'), ('one hundred and fifty-first', '151st'), ('one hundred and fiftieth', '150th'), ('one hundred and forty-ninth', '149th'), ('one hundred and forty-eighth', '148th'), ('one hundred and forty-seventh', '147th'), ('one hundred and forty-sixth', '146th'), ('one hundred and forty-fifth', '145th'), ('one hundred and forty-fourth', '144th'), ('one hundred and forty-third', '143rd'), ('one hundred and forty-second', '142nd'), ('one hundred and forty-first', '141st'), ('one hundred and fortieth', '140th'), ('one hundred and thirty-ninth', '139th'), ('one hundred and thirty-eighth', '138th'), ('one hundred and thirty-seventh', '137th'), ('one hundred and thirty-sixth', '136th'), ('one hundred and thirty-fifth', '135th'), ('one hundred and thirty-fourth', '134th'), ('one hundred and thirty-third', '133rd'), ('one hundred and thirty-second', '132nd'), ('one hundred and thirty-first', '131st'), ('one hundred and thirtieth', '130th'), ('one hundred and twenty-ninth', '129th'), ('one hundred and twenty-eighth', '128th'), ('one hundred and twenty-seventh', '127th'), ('one hundred and twenty-sixth', '126th'), ('one hundred and twenty-fifth', '125th'), ('one hundred and twenty-fourth', '124th'), ('one hundred and twenty-third', '123rd'), ('one hundred and twenty-second', '122nd'), ('one hundred and twenty-first', '121st'), ('one hundred and twentieth', '120th'), ('one hundred and nineteenth', '119th'), ('one hundred and eighteenth', '118th'), ('one hundred and seventeenth', '117th'), ('one hundred and sixteenth', '116th'), ('one hundred and fifteenth', '115th'), ('one hundred and fourteenth', '114th'), ('one hundred and thirteenth', '113th'), ('one hundred and twelfth', '112th'), ('one hundred and eleventh', '111th'), ('one hundred and tenth', '110th'), ('one hundred and ninth', '109th'), ('one hundred and eighth', '108th'), ('one hundred and seventh', '107th'), ('one hundred and sixth', '106th'), ('one hundred and fifth', '105th'), ('one hundred and fourth', '104th'), ('one hundred and third', '103rd'), ('one hundred and second', '102nd'), ('one hundred and first', '101st'), ('one hundredth', '100th'), ('ninety-ninth', '99th'), ('ninety-eighth', '98th'), ('ninety-seventh', '97th'), ('ninety-sixth', '96th'), ('ninety-fifth', '95th'), ('ninety-fourth', '94th'), ('ninety-third', '93rd'), ('ninety-second', '92nd'), ('ninety-first', '91st'), ('ninetieth', '90th'), ('eighty-ninth', '89th'), ('eighty-eighth', '88th'), ('eighty-seventh', '87th'), ('eighty-sixth', '86th'), ('eighty-fifth', '85th'), ('eighty-fourth', '84th'), ('eighty-third', '83rd'), ('eighty-second', '82nd'), ('eighty-first', '81st'), ('eightieth', '80th'), ('seventy-ninth', '79th'), ('seventy-eighth', '78th'), ('seventy-seventh', '77th'), ('seventy-sixth', '76th'), ('seventy-fifth', '75th'), ('seventy-fourth', '74th'), ('seventy-third', '73rd'), ('seventy-second', '72nd'), ('seventy-first', '71st'), ('seventieth', '70th'), ('sixty-ninth', '69th'), ('sixty-eighth', '68th'), ('sixty-seventh', '67th'), ('sixty-sixth', '66th'), ('sixty-fifth', '65th'), ('sixty-fourth', '64th'), ('sixty-third', '63rd'), ('sixty-second', '62nd'), ('sixty-first', '61st'), ('sixtieth', '60th'), ('fifty-ninth', '59th'), ('fifty-eighth', '58th'), ('fifty-seventh', '57th'), ('fifty-sixth', '56th'), ('fifty-fifth', '55th'), ('fifty-fourth', '54th'), ('fifty-third', '53rd'), ('fifty-second', '52nd'), ('fifty-first', '51st'), ('fiftieth', '50th'), ('forty-ninth', '49th'), ('forty-eighth', '48th'), ('forty-seventh', '47th'), ('forty-sixth', '46th'), ('forty-fifth', '45th'), ('forty-fourth', '44th'), ('forty-third', '43rd'), ('forty-second', '42nd'), ('forty-first', '41st'), ('fortieth', '40th'), ('thirty-ninth', '39th'), ('thirty-eighth', '38th'), ('thirty-seventh', '37th'), ('thirty-sixth', '36th'), ('thirty-fifth', '35th'), ('thirty-fourth', '34th'), ('thirty-third', '33rd'), ('thirty-second', '32nd'), ('thirty-first', '31st'), ('thirtieth', '30th'), ('twenty-ninth', '29th'), ('twenty-eighth', '28th'), ('twenty-seventh', '27th'), ('twenty-sixth', '26th'), ('twenty-fifth', '25th'), ('twenty-fourth', '24th'), ('twenty-third', '23rd'), ('twenty-second', '22nd'), ('twenty-first', '21st'), ('twentieth', '20th'), ('nineteenth', '19th'), ('eighteenth', '18th'), ('seventeenth', '17th'), ('sixteenth', '16th'), ('fifteenth', '15th'), ('fourteenth', '14th'), ('thirteenth', '13th'), ('twelfth', '12th'), ('eleventh', '11th'), ('tenth', '10th'), ('ninth', '9th'), ('eighth', '8th'), ('seventh', '7th'), ('sixth', '6th'), ('fifth', '5th'), ('fourth', '4th'), ('third', '3rd'), ('second', '2nd')]
    for key, value in map:
        s = re.sub(re.escape(key), value, s)
    return s


# Functions on sequences of numbers
# NOTE: these take the sequence argument first, like min and max,
# and like standard math notation: \sigma (i = 1..n) fn(i)
# From http://aima.cs.berkeley.edu/python/utils.html
def argmin(seq, fn):
    """Return an element with lowest fn(seq[i]) score; tie goes to first one.
    >>> argmin(['one', 'to', 'three'], len)
    'to'
    """
    best = seq[0]; best_score = fn(best)
    for x in seq:
        x_score = fn(x)
        if x_score < best_score:
            best, best_score = x, x_score
    return best

def argmin_list(seq, fn):
    """Return a list of elements of seq[i] with the lowest fn(seq[i]) scores.
    >>> argmin_list(['one', 'to', 'three', 'or'], len)
    ['to', 'or']
    """
    best_score, best = fn(seq[0]), []
    for x in seq:
        x_score = fn(x)
        if x_score < best_score:
            best, best_score = [x], x_score
        elif x_score == best_score:
            best.append(x)
    return best

def argmin_random_tie(seq, fn):
    """Return an element with lowest fn(seq[i]) score; break ties at random.
    Thus, for all s,f: argmin_random_tie(s, f) in argmin_list(s, f)"""
    best_score = fn(seq[0]); n = 0
    for x in seq:
        x_score = fn(x)
        if x_score < best_score:
            best, best_score = x, x_score; n = 1
        elif x_score == best_score:
            n += 1
            if random.randrange(n) == 0:
                    best = x
    return best

def argmax(seq, fn):
    """Return an element with highest fn(seq[i]) score; tie goes to first one.
    >>> argmax(['one', 'to', 'three'], len)
    'three'
    """
    return argmin(seq, lambda x: -fn(x))

def argmax_list(seq, fn):
    """Return a list of elements of seq[i] with the highest fn(seq[i]) scores.
    >>> argmax_list(['one', 'three', 'seven'], len)
    ['three', 'seven']
    """
    return argmin_list(seq, lambda x: -fn(x))

def argmax_random_tie(seq, fn):
    "Return an element with highest fn(seq[i]) score; break ties at random."
    return argmin_random_tie(seq, lambda x: -fn(x))