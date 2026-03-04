import csv
import time
from typing import List
from athlete import load_old_athletes_to_dict_from_file, load_unique_paris_athletes_from_file
from country import CountryMap, loadCountriesToGlobalDictFromFile, loadParisCountries
from edition import Edition, load_games_to_dict_from_file
from results import Medal, EventResult, load_new_medallists, load_old_event_results_from_file

class Tally:
    def __init__(self, edition_id: int, country_noc: str, number_of_athletes: int, gold_count: int, silver_count: int, bronze_count: int):
        self.edition_id = edition_id
        self.country_noc = country_noc
        self.number_of_athletes = number_of_athletes
        self.gold_count = gold_count
        self.silver_count = silver_count
        self.bronze_count = bronze_count
        self.athlete_ids = set()  # Track unique athletes

    def totalMedals(self) -> int:
        return self.gold_count + self.silver_count + self.bronze_count
    
def tally_medals(editions: dict[int, Edition], results_by_edition: dict[int, List[EventResult]]) -> dict[int, dict[str, Tally]]:
    """
    :return: Dictionary of editions containing a dictionary of tallies by country
    :rtype: dict[int, dict[str, Tally]]

    Team sports medals are counted once per team, not per athlete.
    For example, if 11 athletes win gold in football, that's 1 gold medal for the country.
    """
    tallies: dict[int, dict[str, Tally]] = {}
    for key, _ in editions.items():
        if not key in tallies:
            tallies[key] = {}

    gold_e = Medal.gold
    silver_e = Medal.silver
    bronze_e = Medal.bronze

    # Track which (edition, country, event, medal) combinations we've already counted
    # This prevents counting the same team medal multiple times
    counted_team_medals = set()

    for key, value in results_by_edition.items():
        for result in value:
            if not result.country_noc in tallies[key]:
                tallies[key][result.country_noc] = Tally(key, result.country_noc, 0, 0, 0, 0)

            tally = tallies[key][result.country_noc]
            # Add unique athlete ID to set
            tally.athlete_ids.add(result.athlete_id)
            # Update number_of_athletes to count unique athletes
            tally.number_of_athletes = len(tally.athlete_ids)

            if(result.medal != None):
                # For team sports, only count the medal once per (edition, country, sport, event, medal_type)
                if result.isTeamSport:
                    team_key = (key, result.country_noc, result.sport, result.event, result.medal)
                    if team_key in counted_team_medals:
                        continue  # Already counted this team medal
                    counted_team_medals.add(team_key)

                # Count the medal
                if(result.medal == gold_e):
                    tally.gold_count += 1
                elif(result.medal == silver_e):
                    tally.silver_count += 1
                elif(result.medal == bronze_e):
                    tally.bronze_count += 1

    return tallies

def write_tally_to_file(file_name: str, tallies: dict[int, dict[str, Tally]], editions: dict[int, Edition], countries: CountryMap) -> None:
    with open(file_name, mode="w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["edition", "edition_id", "Country", "NOC", "number_of_athletes", "gold_medal_count", "silver_medal_count", "bronze_medal_count", "total_medals"])
        for _, value in tallies.items():
            for _, tally in value.items():
                data = [
                    editions[tally.edition_id].edition,
                    tally.edition_id,
                    countries.getCountry(tally.country_noc).name, # type: ignore
                    tally.country_noc,
                    tally.number_of_athletes,
                    tally.gold_count,
                    tally.silver_count,
                    tally.bronze_count,
                    tally.totalMedals()
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

# tallies = tally_medals(editions, results)
# write_tally_to_file("tally.csv", tallies, editions, c)

# end_time = time.perf_counter()
# elapsed_time = end_time - start_time
# print(f"Code execution time: {elapsed_time:.4f} seconds")

