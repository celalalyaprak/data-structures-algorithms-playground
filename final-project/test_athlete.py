import unittest

from athlete import *

class TestAthleteId(unittest.TestCase):
    def test_athleteIdEqlSameEverything(self):
        id1 = AthleteUnique(1, "hello", date(2025, 1, 1), "can")
        id2 = AthleteUnique(1, "hello", date(2025, 1, 1), "can")
        self.assertEqual(id1, id2)

    def test_athleteIdEqlDifferentIdSameOther(self):
        id1 = AthleteUnique(1, "hello", date(2025, 1, 1), "can")
        id2 = AthleteUnique(2, "hello", date(2025, 1, 1), "can")
        self.assertEqual(id1, id2)

    def test_athleteIdEqlDifferentName(self):
        id1 = AthleteUnique(1, "hello", date(2025, 1, 1), "can")
        id2 = AthleteUnique(1, "hella", date(2025, 1, 1), "can")
        self.assertNotEqual(id1, id2)

    def test_athleteIdEqlDifferentBorn(self):
        id1 = AthleteUnique(1, "hello", date(2025, 1, 1), "can")
        id2 = AthleteUnique(1, "hello", date(2025, 1, 2), "can")
        self.assertNotEqual(id1, id2)

    def test_athleteIdEqlDifferentCountry(self):
        id1 = AthleteUnique(1, "hello", date(2025, 1, 1), "can")
        id2 = AthleteUnique(1, "hello", date(2025, 1, 1), "usa")
        self.assertNotEqual(id1, id2)

    def test_athleteIdHashSameEverything(self):
        id1 = AthleteUnique(1, "hello", date(2025, 1, 1), "can")
        id2 = AthleteUnique(1, "hello", date(2025, 1, 1), "can")
        h1 = hash(id1)
        h2 = hash(id2)
        self.assertEqual(h1, h2)

    def test_athleteIdHashDifferentIdSameOther(self):
        id1 = AthleteUnique(1, "hello", date(2025, 1, 1), "can")
        id2 = AthleteUnique(2, "hello", date(2025, 1, 1), "can")
        h1 = hash(id1)
        h2 = hash(id2)
        self.assertEqual(h1, h2)

    def test_athleteIdHashDifferentName(self):
        id1 = AthleteUnique(1, "hello", date(2025, 1, 1), "can")
        id2 = AthleteUnique(1, "hella", date(2025, 1, 1), "can")
        h1 = hash(id1)
        h2 = hash(id2)
        if(h1 == h2):
            print("skipping test [test_athleteIdHashDifferentName] hash values were the same")

    def test_athleteIdHashDifferentBorn(self):
        id1 = AthleteUnique(1, "hello", date(2025, 1, 1), "can")
        id2 = AthleteUnique(1, "hello", date(2025, 1, 2), "can")
        h1 = hash(id1)
        h2 = hash(id2)
        if(h1 == h2):
            print("skipping test [test_athleteIdHashDifferentBorn] hash values were the same")

    def test_athleteIdHashDifferentCountry(self):
        id1 = AthleteUnique(1, "hello", date(2025, 1, 1), "can")
        id2 = AthleteUnique(1, "hello", date(2025, 1, 1), "usa")
        h1 = hash(id1)
        h2 = hash(id2)
        if(h1 == h2):
            print("skipping test [test_athleteIdHashDifferentCountry] hash values were the same")

class TestAthlete(unittest.TestCase):
    def test_athleteAgeYearOnly(self):
        a = Athlete(AthleteUnique(1, "a", date(2000, 1, 1), "can"), "male", 0, 0)
        age = a.age_on_date(date(2025, 1, 1))
        self.assertEqual(age, 25)

    def test_athleteAgeMonthHasntHappened(self):
        a = Athlete(AthleteUnique(1, "a", date(2000, 2, 1), "can"), "male", 0, 0)
        age = a.age_on_date(date(2025, 1, 1))
        self.assertEqual(age, 24)

    def test_athleteAgeDayHasntHappened(self):
        a = Athlete(AthleteUnique(1, "a", date(2000, 1, 2), "can"), "male", 0, 0)
        age = a.age_on_date(date(2025, 1, 1))
        self.assertEqual(age, 24)

if __name__ == '__main__':
    unittest.main()