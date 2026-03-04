import unittest

from country import *

class TestCountryMap(unittest.TestCase):
    def test_addOneCountry(self):
        map = CountryMap()
        try:
            map.getCountry("CAN")
        except ValueError:
            pass
        else:
            self.fail()

        map.addCountry("CAN", "Canada")
        try:
            country = map.getCountry("CAN")
            self.assertEqual(country.noc, "CAN")
            self.assertEqual(country.name, "Canada")
        except ValueError:
            self.fail()

    def test_sameIdOnDuplicateAdd(self):
        map = CountryMap()
        map.addCountry("CAN", "Canada")
        canada1 = map.getCountry("CAN")
        map.addCountry("CAN", "Canada")
        canada2 = map.getCountry("CAN")
        self.assertEqual(id(canada1), id(canada2))

    def test_sameIdOneMultipleAdd(self):
        map = CountryMap()
        map.addCountry("CAN", "Canada")
        map.addCountry("USA", "United States")
        canada1 = map.getCountry("CAN")
        map.addCountry("CAN", "Canada")
        map.addCountry("USA", "United States")
        canada2 = map.getCountry("CAN")
        self.assertEqual(id(canada1), id(canada2))


if __name__ == '__main__':
    unittest.main()