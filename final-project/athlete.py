from datetime import date, datetime
import csv
from typing import List, Optional
from enum import Enum
import time
import sys
from conversion import convert_paris_event_to_old
from country import CountryMap, loadCountriesToGlobalDictFromFile, loadParisCountries

class Sex(Enum):
    male = 1,
    female = 2

class AthleteUnique:
    """
    Unique identifier for each athlete. Does not use the `athlete_id`
    or `code` fields found in the `olypmic_athlete_bio.csv` or `athletes.csv`
    files, as they have mismatched ids. Uses names, country, and
    birthdate to determine uniqueness.
    """

    def __init__(self, id: int, name: str, born: Optional[date], country_noc: str):
        self.id = id
        self.name = name
        self.born = born
        self.country_noc = country_noc

    def __eq__(self, other) -> bool:
        return self.name == other.name and self.born == other.born and self.country_noc == other.country_noc
    
    def __hash__(self) -> int:
        return hash((self.name, self.born, self.country_noc))

class Athlete:
    """
    Due to some countries and nationalities not being the same is the paris data
    and the existence of the Refugee team, the athlete will contain both a
    team field of type `Country`, as well as a nationality field of type
    `Country` as well.
    """

    def __init__(self, unique: AthleteUnique, sex: Sex, height: Optional[int], weight: Optional[int]):
        self.unique = unique
        self.sex = sex
        self.height = height
        self.weight = weight

    def age_on_date(self, date: date) -> Optional[int]:
        if(self.unique.born == None):
            return None
        age = date.year - self.unique.born.year
        if (date.month, date.day) < (self.unique.born.month, self.unique.born.day):
            age -= 1
        return age
    
class AthleteMap:
    """
    Liu Yang appears 3 times in the `olympic_athlete_bio.csv` file, all 3 from china.
    They all have different birth dates. One is August 11th 1994, another is January
    4th 1986, and the last has no birth date. Furthermore, the August one is present
    in the paris `athletes.csv` file.

    " Durand" appears more than once in `olympic_athlete.bio.csv`, all from France,
    and all without birth dates

    As a result of this, storing athletes by their ids, AND unique information
    is useful.
    """
    def __init__(self):
        self.athletes_by_id: dict[int, Athlete] = {}
        self.athletes_by_unique: dict[AthleteUnique, Athlete] = {}
        self.paris_events: dict[int, List[str]] = {}

    def add_athlete(self, id: int, athlete: Athlete, check_dupe: bool) -> Optional[Athlete]:
        if not check_dupe:
            self.athletes_by_id[id] = athlete
            self.athletes_by_unique[athlete.unique] = athlete
        else:
            found = self.athletes_by_unique.get(athlete.unique)
            if found == None:
                self.athletes_by_id[id] = athlete
                self.athletes_by_unique[athlete.unique] = athlete
            else:
                # Add the paris id as well
                self.athletes_by_id[id] = found
                return found
        return None

    def get_athlete_by_id(self, id: int) -> Optional[Athlete]:
        if not id in self.athletes_by_id:
            return None
        else:
            return self.athletes_by_id[id]
    
    def add_athlete_paris_events(self, id: int, events: List[str]):
        if id in self.paris_events:
            raise ValueError(f"Duplicate athlete events: {id}")
        self.paris_events[id] = events

    def get_paris_events_by_id(self, id: int) -> List[str]:
        if not id in self.paris_events:
            raise ValueError(f"ID not a known athlete: {id}")
        else:
            return self.paris_events[id]

"""
- Change the format of this column to a date of the form dd-Mon-yyyy for example 25-Feb-2025 would be in the correct format.
- Some data is missing, if that is the case, simply make the data as empty (empty string)
- Some data is incomplete (example has year only) or just not as expected...it is up to you to decide how to deal with these cases. Wherever possible, a reasonable estimate of the birthdate should be made.
"""

MONTHS = {
    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
    'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12,
    'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6, 
    'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12
}

def parse_old_file_birthdate(birthdate_str: str) -> Optional[date]:
    if " " in birthdate_str:
        try:
            parts = birthdate_str.split(' ')
            return date(int(parts[2]), MONTHS[parts[1]], int(parts[0]))
        except:
            if(" or " in birthdate_str):
                index = birthdate_str.find(" or ")
                # January 1st of the first provided year
                return date(int(birthdate_str[index - 4:index]), 1, 1)
            elif("circa" in birthdate_str):
                index = birthdate_str.find("circa ")
                # January 1st of the first provided year
                return date(int(birthdate_str[index + 6:index + 10]), 1, 1)
            elif("c." in birthdate_str):
                index = birthdate_str.find("c. ")
                # January 1st of the first provided year
                return date(int(birthdate_str[index + 3:index + 7]), 1, 1)
            elif("in " in birthdate_str):          
                return None
            else:
                # First day
                return datetime.strptime("1 " + birthdate_str, "%d %B %Y").date()
    # 1900s. While this is more common than 1800s, 1800s will filter out questionable data
    elif "-" in birthdate_str:
        try:
            parts = birthdate_str.split('-')
            if len(parts[2]) == 4:
                year = int(parts[2])
            else:
                yy = int(parts[2])
                year = 2000 + yy if yy <= 24 else 1900 + yy
            return date(year, MONTHS[parts[1]], int(parts[0]))
        except:
            yy = int(birthdate_str[4:6])
            year = 2000 + yy if yy <= 24 else 1900 + yy
            # First day
            return date(year, MONTHS[birthdate_str[0:3]], 1)
    # No birth date information
    elif len(birthdate_str) == 0:
        return None
    # Only the year.
    else:
        # Use January 1st
        return date(int(birthdate_str), 1, 1)
 
def load_old_athletes_to_dict_from_file(file_name: str, countries: CountryMap) -> AthleteMap:
    """
    olympic_athlete_bio.csv file layout
    0 -> athlete_id
    1 -> name
    2 -> sex
    3 -> birthdate
    4 -> height
    5 -> weight
    6 -> country
    7 -> country_noc
    """
    athletes = AthleteMap()
    with open(file_name, mode='r', encoding="utf-8-sig") as file:
        csv_reader = csv.reader(file)
        # layout is already known so just skip the header
        _ = next(csv_reader)

        sex_male = Sex.male
        sex_female = Sex.female

        for row in csv_reader:
            birthdate_str: str = row[3]
            id: int = int(row[0])
            name: str = sys.intern(row[1].lower()) # normalize with paris data
            born: Optional[date] = parse_old_file_birthdate(birthdate_str)
            sex: Sex = sex_male if row[2] == "Male" else sex_female
            height: Optional[int] = None if len(row[4]) == 0 else int(row[4])
            weight: Optional[int] = None
            if("-" in row[5]):
                index = row[5].find("-")
                lhs = int(row[5][0:index])
                rhs = int(row[5][index+1:len(row[5])])
                weight = int((lhs + rhs) / 2)
            elif(", " in row[5]):
                index = row[5].find(", ")
                lhs = int(row[5][0:index])
                rhs = int(row[5][index+2:len(row[5])])
                weight = int((lhs + rhs) / 2)
            elif("," in row[5]):
                index = row[5].find(",")
                lhs = int(row[5][0:index])
                rhs = int(row[5][index+1:len(row[5])])
                weight = int((lhs + rhs) / 2)
            else:
                weight = None if len(row[5]) == 0 else int(row[5])  
            country_noc: str = sys.intern(row[7]) # so many repeats
            if(countries.getCountry(country_noc) == None):
                countries.addCountry(country_noc, row[6])

            # Missing first names, and too many collisions. This is a very rare case.
            if name.startswith(" "): 
                name = row[0] + name

            athleteId = AthleteUnique(id, name, born, country_noc)
            athlete = Athlete(athleteId, sex, height, weight)
            athletes.add_athlete(id, athlete, False)
        return athletes
    
def format_paris_name(paris_name: str) -> str:
    """
    Convert Paris name format "LASTNAME Firstname" to "Firstname Lastname".
    """
    if not paris_name or not paris_name.strip():
        return ""

    parts = paris_name.strip().split()
    if len(parts) < 2:
        return paris_name.strip().title()

    def is_lastname_part(part):
        uppercase_count = sum(1 for c in part if c.isupper())
        if uppercase_count >= 2:
            return True
        if part.isupper():
            return True
        if part.lower() in ['van', 'de', 'el', 'la', 'le', 'del', 'di', 'da', 'dos', 'das']:
            return True
        return False

    lastname_parts = []
    firstname_parts = []
    found_firstname = False

    for part in parts:
        if not found_firstname and is_lastname_part(part):
            if part.lower() in ['van', 'de', 'el', 'la', 'le', 'del', 'di', 'da', 'dos', 'das']:
                lastname_parts.append(part.lower())
            else:
                lastname_parts.append(part.title())
        else:
            found_firstname = True
            firstname_parts.append(part)

    if not firstname_parts:
        if len(lastname_parts) >= 2:
            return lastname_parts[-1] + " " + " ".join(lastname_parts[:-1])
        return paris_name.strip()

    lastname = " ".join(lastname_parts)
    firstname = " ".join(firstname_parts)

    return firstname + " " + lastname if lastname else firstname

def load_unique_paris_athletes_from_file(file_name: str, existing_athletes: AthleteMap, countries: CountryMap) -> AthleteMap:
    """
    paris/athletes.csv file layout
    0 -> code
    1 -> current
    2 -> name
    3 -> name_short
    4 -> name_tv
    5 -> gender
    6 -> function
    7 -> country_code
    8 -> country
    9 -> country_long
    10 -> nationality
    11 -> nationality_long
    12 -> nationality_code
    13 -> height
    14 -> weight
    15 -> disciplines
    16 -> events
    17 -> birth_date
    18 -> birth_place
    19 -> birth_country
    20 -> residence_place
    21 -> residence_country
    """
    with open(file_name, mode='r', encoding="utf-8-sig") as file:   
        csv_reader = csv.reader(file)
        # layout is already known so just skip the header
        _ = next(csv_reader)

        sex_male = Sex.male
        sex_female = Sex.female
        for row in csv_reader:
            birthdate_str: str = row[17]
            birthdate_parts = birthdate_str.split("-")
            birthdate = date(int(birthdate_parts[0]), int(birthdate_parts[1]), int(birthdate_parts[2]))
            sex: Sex = sex_male if row[5] == "Male" else sex_female

            height: Optional[int] = None if len(row[13]) == 0 else int(row[13])
            weight: Optional[int] = None if len(row[14]) == 0 else int(row[14])
            if(height == 0):
                height = None
            if(weight == 0):
                weight = None
            
            country_noc = sys.intern(row[7])
            if(countries.getCountry(country_noc) == None):
                countries.addCountry(country_noc, row[8])
            # name_tv is better for the actual name as it should align properly with first last
            # Fall back to name if name_tv is empty (need to format it from LAST First to First Last)
            if row[4].strip():
                athlete_name = row[4]
            else:
                athlete_name = format_paris_name(row[2])
            # Normalize multiple spaces to single space
            athlete_name = ' '.join(athlete_name.split())
            athleteId = AthleteUnique(int(row[0]), sys.intern(athlete_name.lower()), birthdate, country_noc)
            athlete = Athlete(athleteId, sex, height, weight)
            existing = existing_athletes.add_athlete(athleteId.id, athlete, True)
            if existing != None:
                if existing.height == None and height != None:
                    existing.height = height
                if existing.weight == None and weight != None:
                    existing.weight = weight

            # starts and ends with []
            # Necessary for event results
            disciplines_str = row[15][1:len(row[15]) - 1]
            if disciplines_str.startswith("'"):
                discipline = disciplines_str[1:disciplines_str.find("'", 1)]
            elif disciplines_str.startswith('"'):
                discipline = disciplines_str[1:disciplines_str.find('"', 1)]
            else:
                discipline = disciplines_str.split(",")[0].strip().strip("'\"")

            events = row[16][1:len(row[16]) - 1].split(", ")
            for i in range(len(events)):
                if(events[i].startswith('"')): # Also ends with
                    events[i] = events[i][1:len(events[i]) - 1]
                elif(events[i].startswith("'")): # Also ends with
                    events[i] = events[i][1:len(events[i]) - 1]
                events[i] = convert_paris_event_to_old(events[i], discipline)

            existing_athletes.add_athlete_paris_events(athleteId.id, events)
            
    return existing_athletes

def birth_date_to_str(date: Optional[date]) -> str:
    if(date == None):
        return ""

    return date.strftime("%d-%b-%Y")

# Define particles once at module level for performance
_NAME_PARTICLES = frozenset({'van', 'von', 'de', 'el', 'la', 'le', 'del', 'di', 'da', 'dos', 'das', 'der', 'den', 'ben', 'bin', 'al', 'zu', 'ten', 'af', 'op'})
_COMBINING_DOT = '\u0307'

def _title_case_part(part: str) -> str:
    """
    Apply title case to a single name part, handling Turkish İ, apostrophes, and Mc/Mac prefixes.
    """
    if not part:
        return part
    if len(part) == 1:
        return part.upper()

    # Check for Turkish İ at start (i + combining dot U+0307)
    if len(part) > 1 and part[0] == 'i' and part[1] == _COMBINING_DOT:
        return 'İ' + part[2:].lower()

    # Handle apostrophes (O'Brien, D'Almeida, etc.)
    # Right single quote ' (U+2019) and regular apostrophe '
    if "'" in part or '\u2019' in part:
        # Split on apostrophes, title case each segment
        segments = []
        current = []
        for char in part:
            if char in ("'", '\u2019'):
                if current:
                    seg = ''.join(current)
                    segments.append(seg[0].upper() + seg[1:].lower() if len(seg) > 1 else seg.upper())
                    current = []
                segments.append(char)
            else:
                current.append(char)
        if current:
            seg = ''.join(current)
            segments.append(seg[0].upper() + seg[1:].lower() if len(seg) > 1 else seg.upper())
        return ''.join(segments)

    # Handle Mc/Mac prefix (McKenzie, McDonald, MacGregor, etc.)
    part_lower = part.lower()
    if len(part) > 2 and part_lower.startswith('mc'):
        # McKenzie -> Mc + Kenzie -> Mc + capitalize(kenzie)
        return 'Mc' + part[2].upper() + part[3:].lower()
    elif len(part) > 3 and part_lower.startswith('mac'):
        # MacGregor -> Mac + Gregor -> Mac + capitalize(gregor)
        return 'Mac' + part[3].upper() + part[4:].lower()

    # Standard title case
    return part[0].upper() + part[1:].lower()

def smart_title_name(name: str) -> str:
    """
    Apply title case to name while keeping particles lowercase.
    Preserves Turkish İ and other special unicode characters.
    """
    words = name.split()
    if not words:
        return name

    result = []
    for i, word in enumerate(words):
        if not word:
            result.append(word)
            continue

        # Check if it's a particle (only need to lower for comparison if it might be one)
        if i > 0 and len(word) <= 3:
            word_lower = word.lower()
            if word_lower in _NAME_PARTICLES:
                result.append(word_lower)
                continue

        # Single character - just uppercase
        if len(word) == 1:
            result.append(word.upper())
            continue

        # Handle hyphenated names
        if '-' in word:
            parts = word.split('-')
            titled_parts = [_title_case_part(part) for part in parts]
            result.append('-'.join(titled_parts))
        else:
            # Use helper function for title case
            result.append(_title_case_part(word))

    return ' '.join(result)

def write_athletes_to_file(file_name: str, athletes: AthleteMap, countries: CountryMap):
    with open(file_name, mode="w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["athlete_id", "name", "sex", "born", "height", "weight", "country", "country_noc"])
        for _, value in athletes.athletes_by_unique.items():
            data = [
                value.unique.id,
                smart_title_name(value.unique.name),
                "Male" if value.sex == Sex.male else "Female",
                birth_date_to_str(value.unique.born),
                value.height if value.height != None else "",
                value.weight if value.weight != None else "",
                " " + countries.getCountry(value.unique.country_noc).name, # type: ignore - add leading space
                value.unique.country_noc
            ]
            writer.writerow(data)

# start_time = time.perf_counter()
# c = loadCountriesToGlobalDictFromFile("olympics_country.csv")
# loadParisCountries("paris/nocs.csv", c)
# loaded = load_old_athletes_to_dict_from_file("olympic_athlete_bio.csv", c)
# load_unique_paris_athletes_from_file("paris/athletes.csv", loaded, c)
# write_athletes_to_file("athlete.csv", loaded, c)
# end_time = time.perf_counter()
# elapsed_time = end_time - start_time
# print(f"Code execution time: {elapsed_time:.4f} seconds")