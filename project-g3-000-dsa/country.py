import csv
from typing import Optional

class Country:
    """
    Structure representing a player or team's country / nationality.
    This can be distinct, separating a player's country and nationality for
    those who are part of the Refugee Olympic Team.
    """
    def __init__(self, noc: str, name: str):
        self.noc: str = noc
        self.name: str = name

class CountryMap:
    def __init__(self):
        self._dict: dict[str, Country] = {}

    def addCountry(self, noc: str, name: str) -> None:
        """
        Add a new country to the global country dictionary if it doesn't
        already exist
        """
        if noc in self._dict:
            # Already contains, and we don't want to replace the object. 
            # We want "pointer stability"
            pass 
        else:
            country = Country(noc, name)
            self._dict[noc] = country

    def getCountry(self, noc: str) -> Optional[Country]:
        """
        Rather than have an athlete / event / team store unique `Country` instances,
        we can cache them. This reduces the likelihood of forgetting to set a field.
        This also gives the added benefit of keeping all country data in cache.
        """
        if noc in self._dict:
            return self._dict[noc]
        else:
            return None

def loadCountriesToGlobalDictFromFile(file_name: str) -> CountryMap:
    with open(file_name, mode='r', encoding="utf-8-sig") as file:
        csv_reader = csv.reader(file)
        # layout is already known so just skip the header
        _ = next(csv_reader)
        map = CountryMap()
        for row in csv_reader:
            if row[1] == "ROC":
                continue
            map.addCountry(row[0], row[1])
        return map
    
def loadParisCountries(file_name: str, country_map: CountryMap) -> CountryMap:
    with open(file_name, mode='r', encoding="utf-8-sig") as file:
        csv_reader = csv.reader(file)
        # layout is already known so just skip the header
        _ = next(csv_reader)
        for row in csv_reader:
            country_map.addCountry(row[0], row[2])
        return country_map
    
def write_countries_to_file(file_name: str, country_map: CountryMap) -> None:
    with open(file_name, mode="w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["noc", "country"])
        # Sort by country name (case-insensitive)
        sorted_countries = sorted(country_map._dict.values(), key=lambda c: c.name.lower())
        for value in sorted_countries:
            data = [
                value.noc,
                value.name
            ]
            writer.writerow(data)
    
# c = loadCountriesToGlobalDictFromFile("olympics_country.csv")
# loadParisCountries("paris/nocs.csv", c)
# write_countries_to_file("country.csv", c)
    
