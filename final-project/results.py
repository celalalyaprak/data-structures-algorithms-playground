import csv
import sys
import time
from typing import List, Optional
from enum import Enum

from athlete import AthleteMap, load_old_athletes_to_dict_from_file, load_unique_paris_athletes_from_file, smart_title_name
from conversion import convert_paris_event_to_old, is_team_sport
from country import loadCountriesToGlobalDictFromFile, loadParisCountries
from edition import Edition, load_games_to_dict_from_file

class Medal(Enum):
    gold = 1,
    silver = 2,
    bronze = 3

class EventResult:
    def __init__(self, edition_id: int, country_noc: str, sport: str, event: str, result_id: int, athlete_id: int, pos: Optional[str], medal: Optional[Medal], isTeamSport: bool, age: Optional[int]):
        self.edition_id = edition_id
        self.country_noc = country_noc
        self.sport = sport
        self.event = event
        self.result_id = result_id
        self.athlete_id = athlete_id
        self.pos = pos
        self.medal = medal
        self.isTeamSport = isTeamSport
        self.age = age

def load_old_event_results_from_file(file_name: str, athletes: AthleteMap, editions: dict[int, Edition]) -> dict[int, List[EventResult]]:
    """
    olympic_athlete_bio.csv file layout
    0 -> edition
    1 -> edition_id
    2 -> country_noc
    3 -> sport
    4 -> event
    5 -> result_id
    6 -> athlete
    7 -> athlete_id
    8 -> pos
    9 -> medal
    10 -> isTeamSport
    """
    
    edition_results: dict[int, List[EventResult]] = {}
    for key, _ in editions.items():
        edition_results[key] = []
    with open(file_name, mode='r', encoding="utf-8-sig") as file:
        csv_reader = csv.reader(file)
        # layout is already known so just skip the header
        _ = next(csv_reader)

        gold_str = "Gold"
        silver_str = "Silver"
        bronze_str = "Bronze"
        gold_e = Medal.gold
        silver_e = Medal.silver
        bronze_e = Medal.bronze

        i: int = 2
        for row in csv_reader:
            athlete_id = int(row[7])

            athlete = athletes.get_athlete_by_id(athlete_id)
            if(athlete == None): # No data on this athlete, so skip
                continue
            age: Optional[int] = None
            edition_id = int(row[1])
            if(editions[edition_id].start_date != None):
                # if the athlete's birthday is during the olympics add the age as if their birthdate had happened before the olympics began.
                edition = editions[edition_id]
                if edition.end_date and athlete.unique.born:
                    # Check if birthday falls during Olympics
                    start = edition.start_date
                    end = edition.end_date
                    bday_month_day = (athlete.unique.born.month, athlete.unique.born.day)
                    start_month_day = (start.month, start.day)
                    end_month_day = (end.month, end.day)

                    # If birthday is between start and end (inclusive), use end date for age calc
                    if start_month_day <= bday_month_day <= end_month_day:
                        age = athlete.age_on_date(end) # type: ignore
                    else:
                        age = athlete.age_on_date(start) # type: ignore
                else:
                    age = athlete.age_on_date(editions[edition_id].start_date) # type: ignore
            
            medal: Optional[Medal] = None
            if(row[9] == gold_str):
                medal = gold_e
            elif(row[9] == silver_str):
                medal = silver_e
            elif(row[9] == bronze_str):
                medal = bronze_e

            result = EventResult(edition_id, sys.intern(row[2]), sys.intern(row[3]), sys.intern(row[4]), int(row[5]), athlete_id, sys.intern(row[8]), medal, row[10] == "True", age)
            edition_results[edition_id].append(result)

    return edition_results

def load_new_medallists(file_name: str, edition_results: dict[int, List[EventResult]], athletes: AthleteMap, editions: dict[int, Edition]) -> dict[int, List[EventResult]]:
    """
    paris/medallists.csv file layout
    0 -> medal_date
    1 -> medal_type
    2 -> medal_code
    3 -> name
    4 -> gender
    5 -> country_code
    6 -> country
    7 -> country_long
    8 -> nationality_code
    9 -> nationality
    10 -> nationality_long
    11 -> team
    12 -> team_gender
    13 -> discipline
    14 -> event
    15 -> event_type
    16 -> url_event
    17 -> birth_date
    18 -> code_athlete
    19 -> code_team
    20 -> is_medallist
    """

    gold_str = "Gold Medal"
    silver_str = "Silver Medal"
    bronze_str = "Bronze Medal"
    gold_e = Medal.gold
    silver_e = Medal.silver
    bronze_e = Medal.bronze
    edition_id = 63 # Paris 2024 summer

    # First pass: count medals per event to detect ties
    from collections import defaultdict
    event_medal_counts = defaultdict(lambda: {'gold': 0, 'silver': 0, 'bronze': 0})

    with open(file_name, mode='r', encoding="utf-8-sig") as file:
        csv_reader = csv.reader(file)
        _ = next(csv_reader)
        for row in csv_reader:
            discipline = row[13]
            event = convert_paris_event_to_old(row[14], discipline)
            medal_type = row[1]
            if medal_type == gold_str:
                event_medal_counts[event]['gold'] += 1
            elif medal_type == silver_str:
                event_medal_counts[event]['silver'] += 1
            elif medal_type == bronze_str:
                event_medal_counts[event]['bronze'] += 1

    # Second pass: load medallists with proper positions
    with open(file_name, mode='r', encoding="utf-8-sig") as file:
        csv_reader = csv.reader(file)
        _ = next(csv_reader)

        for row in csv_reader:
            athlete_id = int(row[18])

            athlete = athletes.get_athlete_by_id(athlete_id)
            if(athlete == None): # No data on this athlete, so skip
                continue

            age: Optional[int] = None
            if(editions[edition_id].start_date != None):
                edition = editions[edition_id]
                if edition.end_date and athlete.unique.born:
                    # Check if birthday falls during Olympics
                    start = edition.start_date
                    end = edition.end_date
                    bday_month_day = (athlete.unique.born.month, athlete.unique.born.day)
                    start_month_day = (start.month, start.day)
                    end_month_day = (end.month, end.day)

                    # If birthday is between start and end (inclusive), use end date for age calc
                    if start_month_day <= bday_month_day <= end_month_day:
                        age = athlete.age_on_date(end) # type: ignore
                    else:
                        age = athlete.age_on_date(start) # type: ignore
                else:
                    age = athlete.age_on_date(editions[edition_id].start_date) # type: ignore

            medal: Optional[Medal] = None
            pos: Optional[str] = None
            discipline = row[13]
            event = convert_paris_event_to_old(row[14], discipline)

            if(row[1] == gold_str):
                medal = gold_e
                pos = "=1" if event_medal_counts[event]['gold'] > 1 else "1"
            elif(row[1] == silver_str):
                medal = silver_e
                pos = "=2" if event_medal_counts[event]['silver'] > 1 else "2"
            elif(row[1] == bronze_str):
                medal = bronze_e
                pos = "=3" if event_medal_counts[event]['bronze'] > 1 else "3"

            result_id = abs(hash(row[16])) # Use absolute value to avoid negative IDs
            result = EventResult(edition_id, sys.intern(row[5]), sys.intern(row[13]), event, result_id, athlete_id, pos, medal, is_team_sport(event), age)
            edition_results[edition_id].append(result)

    return edition_results

def load_paris_athlete_events(paris_medallists_file: str, edition_results: dict[int, List[EventResult]], athletes: AthleteMap, editions: dict[int, Edition]) -> dict[int, List[EventResult]]:
    """
    Load ALL Paris athlete events from athletes.paris_events (populated during athlete loading).
    This adds non-medalist participants to complete the Paris 2024 results.
    """
    edition_id = 63  # Paris 2024 summer

    # First, build a set of (athlete_id, event) combinations already added from medallists
    existing_entries = set()
    for result in edition_results[edition_id]:
        existing_entries.add((result.athlete_id, result.event))

    # Read medallists to get sport discipline for each event
    event_to_sport: dict[str, str] = {}
    with open(paris_medallists_file, mode='r', encoding="utf-8-sig") as file:
        csv_reader = csv.reader(file)
        _ = next(csv_reader)  # skip header
        for row in csv_reader:
            discipline = row[13]
            event = convert_paris_event_to_old(row[14], discipline)
            sport = sys.intern(discipline)
            event_to_sport[event] = sport

    # Generate a unique result_id counter starting after existing max
    max_result_id = 0
    for results_list in edition_results.values():
        for result in results_list:
            if result.result_id > max_result_id:
                max_result_id = result.result_id
    next_result_id = max_result_id + 1

    # Iterate through all athletes and their Paris events
    for athlete_id, athlete in athletes.athletes_by_id.items():
        if athlete_id not in athletes.paris_events:
            continue  # Not a Paris athlete

        events = athletes.paris_events[athlete_id]
        for event in events:
            # Skip if this (athlete, event) already exists (from medallists)
            if (athlete_id, event) in existing_entries:
                continue

            # Get sport from event mapping
            # Special case: "Relay Only Athlete" is always Swimming
            if event == "Relay Only Athlete":
                sport = "Swimming"
            else:
                sport = event_to_sport.get(event, "")
                if not sport:
                    continue  # Skip events without sport info

            # Calculate age
            age: Optional[int] = None
            if editions[edition_id].start_date is not None:
                edition = editions[edition_id]
                if edition.end_date and athlete.unique.born:
                    # Check if birthday falls during Olympics
                    start = edition.start_date
                    end = edition.end_date
                    bday_month_day = (athlete.unique.born.month, athlete.unique.born.day)
                    start_month_day = (start.month, start.day)
                    end_month_day = (end.month, end.day)

                    # If birthday is between start and end (inclusive), use end date for age calc
                    if start_month_day <= bday_month_day <= end_month_day:
                        age = athlete.age_on_date(end)  # type: ignore
                    else:
                        age = athlete.age_on_date(start)  # type: ignore
                else:
                    age = athlete.age_on_date(editions[edition_id].start_date)  # type: ignore

            # Create result entry (no medal, no position for non-medallists)
            result = EventResult(
                edition_id,
                athlete.unique.country_noc,
                sport,
                event,
                next_result_id,
                athlete_id,
                None,  # no position
                None,  # no medal
                is_team_sport(event),
                age
            )
            edition_results[edition_id].append(result)
            existing_entries.add((athlete_id, event))
            next_result_id += 1

    return edition_results

def medal_to_str(medal: Optional[Medal]) -> str:
    if medal == None:
        return ""
    elif medal == Medal.gold:
        return "Gold"
    elif medal == Medal.silver:
        return "Silver"
    elif medal == Medal.bronze:
        return "Bronze"

def write_results_to_file(file_name: str, results: dict[int, List[EventResult]], editions: dict[int, Edition], athletes: AthleteMap) -> None:
    # reorder
    paris_results = results[63]
    del results[63]
    results[63] = paris_results

    with open(file_name, mode="w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["edition", "edition_id", "country_noc", "sport", "event", "result_id", "athlete", "athlete_id", "pos", "medal", "isTeamSport", "age"])
        for _, value in results.items():
            for result in value:
                start_date = editions[result.edition_id].start_date
                age: Optional[int] = None
                if start_date != None:
                    athlete = athletes.get_athlete_by_id(result.athlete_id)
                    edition = editions[result.edition_id]
                    if edition.end_date and athlete.unique.born:
                        # Check if birthday falls during Olympics
                        end = edition.end_date
                        bday_month_day = (athlete.unique.born.month, athlete.unique.born.day)
                        start_month_day = (start_date.month, start_date.day)
                        end_month_day = (end.month, end.day)

                        # If birthday is between start and end (inclusive), use end date for age calc
                        if start_month_day <= bday_month_day <= end_month_day:
                            age = athlete.age_on_date(end)
                        else:
                            age = athlete.age_on_date(start_date)
                    else:
                        age = athlete.age_on_date(start_date)
                data = [
                    editions[result.edition_id].edition,
                    result.edition_id,
                    result.country_noc,
                    result.sport,
                    result.event,
                    result.result_id,
                    smart_title_name(athletes.get_athlete_by_id(result.athlete_id).unique.name), # type: ignore
                    result.athlete_id,
                    "" if result.pos == None else result.pos,
                    medal_to_str(result.medal),
                    result.isTeamSport,
                    "" if age == None else age
                ]
                writer.writerow(data)

# start_time = time.perf_counter()
# c = loadCountriesToGlobalDictFromFile("olympics_country.csv")
# loadParisCountries("paris/nocs.csv", c)
# editions = load_games_to_dict_from_file("olympics_games.csv")
# athletes = load_old_athletes_to_dict_from_file("olympic_athlete_bio.csv", c)
# athletes = load_unique_paris_athletes_from_file("paris/athletes.csv", athletes, c)
# results = load_old_event_results_from_file("olympic_athlete_event_results.csv",  athletes, editions)
# results = load_new_medallists("paris/medallists.csv", results, athletes, editions)
# write_results_to_file("results.csv", results, editions, athletes)
# end_time = time.perf_counter()
# elapsed_time = end_time - start_time
# print(f"Code execution time: {elapsed_time:.4f} seconds")