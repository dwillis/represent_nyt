import unittest
from projects.represent.geocode import geocode_address

class GeocodeTestCase(unittest.TestCase):
    
    def testLocation(self):
        result = geocode_address('620 8th Ave 10018')
        expecting = {'street': '8th', 'city': 'New York', 'state': 'NY', 'zip': '10018', 'address': '620 8th Ave', 'lat': '40.755951', 'long': '-73.990726'}
        self.assertEqual(result, expecting, 'Got %s. Expected %s' % (result, expecting))
        
    def testZipCodes(self):
        check('620 8th Ave, New York, NY', 'zip', '10018')
        check('220 madison ave', 'zip', '10016')
        check('120 1st place', 'zip', '11231')
        
    def testCityNames(self):
        check('120 1st place', 'city', 'Brooklyn')
        check('220 madison ave', 'city', 'New York')
        check('1731 Crosby Ave', 'city', 'Bronx')
        check('524 Port Richmond Ave', 'city', 'Staten Island')
        check('36-21 Ditmars Blvd 11105', 'city', 'Astoria')
        check('3949 48th Ave, Sunnyside, NY 11104', 'city', 'Sunnyside')
        
    def testPartialAddresses(self):
        check('120 1st place', 'zip', '11231')
        check('120 1st place, Brooklyn', 'zip', '11231')
        check('120 1st place, Brooklyn NY', 'zip', '11231')
        check('120 1st place, Brooklyn NY 11231', 'zip', '11231')
        
    def testPunctuationAndWhitespace(self):
        check('620 8th Ave, Brooklyn, NY', 'zip', '11215')
        check('620 8th Ave Brooklyn NY', 'zip', '11215')
        check('620 8th Ave Brooklyn, NY', 'zip', '11215')
        check('  620  8th   Ave   Brooklyn, NY ', 'zip', '11215')
        check('  620  8th   Ave   Brooklyn  , NY ', 'zip', '11215')
        check('620 8th Ave, Brooklyn, NY 11215', 'zip', '11215')
        check('620 8th Ave, Brooklyn, NY, 11215', 'zip', '11215')
        check('620 8th Ave, Brooklyn NY, 11215', 'zip', '11215')
        check('620 8th Ave Brooklyn NY, 11215', 'zip', '11215')
        check('620 8th Ave 11215', 'zip', '11215')
        check('620 8th Ave, 11215', 'zip', '11215')

    def testZipPlusFour(self):
        check('220 Madison Ave 10016-3415', 'zip', '10016')
        check('220 Madison Ave New York NY 10016-3415', 'zip', '10016')

    def testOrdinals(self):
        check('620 Eighth ave 10018', 'zip', '10018')
        check('120 First place 11231', 'zip', '11231')
        
    def testZipCodeBasedDisambiguation(self):
        check('620 Eighth ave 10018', 'zip', '10018')
        check('620 Eighth ave 11215', 'zip', '11215')
        check('100 1st st 11231', 'zip', '11231')
        check('100 1st st 10009', 'zip', '10009')
        check('100 1st st 11211', 'zip', '11211')
        
    def testZipCodeBasedDisambiguationWithCityAndState(self):
        check('620 Eighth ave New York, NY 10018', 'zip', '10018')
        check('620 Eighth ave New York 10018', 'zip', '10018')
        check('620 Eighth ave Brooklyn, NY 11215', 'zip', '11215')
        check('620 Eighth ave Brooklyn 11215', 'zip', '11215')
        
    def testAddressWhereStreetNameIsAlsoACityName(self):
        check("110-28 Astoria Blvd", 'zip', '11369')
        check("90-15 Queens Blvd.", 'zip', '11373')
 
    def testProblemAdresses(self):
        check("2227 35th St, Astoria, NY", 'zip', '11105') # Gebeloff
        # TODO: check("2432 Grand Concourse", 'zip', '10458')

    def TODO__testAddressWithStreetTypeInStreetName(self):
        check("1260 Avenue of the Americas, 10020", 'zip', '10020')
        check("1260 Avenue of the Americas", 'zip', '10020')
       
    def testInputWithNewZipCodes(self):
        check('200 E 63RD ST 10065, New York, NY', 'city', 'New York')
        check('200 E 69TH ST 10021, New York, NY', 'city', 'New York')
        check('200 E 77TH ST 10075, New York, NY', 'city', 'New York')
        check('308 East 79 Street, New York, NY 10075', 'city', 'New York') # TIME2improve@aol.com
 
    def TODO__testOutputWithNewZipCodes(self):
        check('200 E 63RD ST 10065', 'zip', '10065')
        check('200 E 69TH ST 10021', 'zip', '10021')
        check('200 E 77TH ST 10075', 'zip', '10075')
        check('308 East 79 Street, New York, NY', 'zip', '10075') # TIME2improve@aol.com
        
    def testNewUpperEastSideZipCode(self):
        check("1755 York Ave New York, NY", 'city', 'New York') # Gerst
        check("1755 York Ave 10128", 'zip', '10128')
        check("1755 York Ave New York, NY", 'zip', '10128')

    def testDefaultIsManhattan(self):
        check('620 Eighth ave', 'zip', '10018')

    def testCityBasedDisambiguation(self):
        check('620 Eighth ave New York', 'zip', '10018')
        check('620 Eighth ave Brooklyn', 'zip', '11215')
        
    def TODO__testNearbyZipCodeBasedDisambiguation(self):
        check('620 Eighth ave 10016', 'zip', '10018')
        check('620 Eighth ave 11211', 'zip', '11215')
        check('620 Eighth ave 10016', 'street', '620 8th Ave')
        check('620 Eighth ave 11211', 'street', '620 8th Ave')
    
    def TODO__testStreetNamesThatLookLikeStreetTypes(self):
        check('1 CENTRAL PARK WEST NEW YORK NY 10023', 'zip', '10023')
        check('101 CENTRAL PARK NEW YORK NY 10023', 'zip', '10023')
        check('110 Central Park South New York NY 10019', 'zip', '10019')
        check('150 Central Park South', 'zip', '10019')
        check('150 Central Park South', 'address', '150 Central Park South')
        check('75 Prospect Park West 11215', 'address', '75 Prospect Park West') # Emily's brother
        
    def testQueensIsNotHarlem(self):
        check('141-16 56th Ave Flushing NY 11355', 'zip', '11355')

def check(address, field, zip):
    result = geocode_address(address)
    assert result[field] == zip, "wrong %s for %s. Got %s. Expected %s" % (field, address, result[field], zip)


if __name__ == "__main__":
    unittest.main()
