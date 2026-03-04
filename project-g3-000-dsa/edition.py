import csv
from datetime import date, datetime
import sys
from typing import List, Optional

"""
You can google for the exact date of the Paris 2024 Olympics as well as the Milano-Cortina 2026 Olympics and use that info in your program

In the olympic_games.csv some rows have years in the dates and some do not. Clean the data by changing all dates to this format:
dd-Mon-yyyy
For the competition date format the range as:
dd-Mon-yyyy to dd-Mon-yyyy

Tokyo 2020 summer olympics started in 2021, not 2020

start_date and end_date entries that have a single digit date have a leading space. Remove that.
"""

class Edition:
    """
    """

    def __init__(self, id: int, edition: str, edition_url: str, year: int, city: str, country_flag_url: str, country_noc: str, start_date: Optional[date], end_date: Optional[date], competition_start: Optional[date], competition_end: Optional[date], is_held: Optional[str]):
        self.id = id
        self.edition = edition
        self.edition_url = edition_url
        self.year = year
        self.city = city
        self.country_flag_url = country_flag_url
        self.country_noc = country_noc
        self.start_date = start_date
        self.end_date = end_date
        self.competition_start = competition_start
        self.competition_end = competition_end
        self.is_held = is_held

MONTHS = {
    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
    'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12,
    'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6, 
    'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12
}

def date_from_edition_date_str(date_str: str, year: int) -> date:
    """
    start_date or end_date
    """
    if date_str.startswith(" "):
        date_str = date_str[1:]
    
    found = date_str.find(" 2021") # silly
    if found != -1:
        date_str = date_str[0:found]

    parts = date_str.split(" ")
    return date(year, MONTHS[parts[1]], int(parts[0]))
    

def load_games_to_dict_from_file(file_name: str) -> dict[int, Edition]:
    """
    olympic_athlete_bio.csv file layout
    0 -> edition
    1 -> edition_id
    2 -> edition_url
    3 -> year
    4 -> city
    5 -> country_flag_url
    6 -> country_noc
    7 -> start_date
    8 -> end_date
    9 -> competition_date
    10 -> isHeld
    """
    games: dict[int, Edition] = {}
    with open(file_name, mode='r', encoding="utf-8-sig") as file:
        csv_reader = csv.reader(file)
        # layout is already known so just skip the header
        _ = next(csv_reader)

        for row in csv_reader:
            edition = sys.intern(row[0])
            id = int(row[1])
            year = int(row[3])
            is_held: Optional[str] = None
            if(len(row[10]) > 0):
                is_held = row[10]

            start_date: Optional[date] = None
            if(len(row[7]) > 0):
                start_date = date_from_edition_date_str(row[7], year)

            end_date: Optional[date] = None
            if(len(row[8]) > 0):
                end_date = date_from_edition_date_str(row[8], year)
            
            competition_start: Optional[date] = None
            competition_end: Optional[date] = None
            if(row[9] == "—"): # stupid emdash
                # When writing we can send this back to just "-" like before
                competition_start = start_date
                competition_end = end_date
            else:
                comp_parts = row[9].split(" – ")
                if comp_parts[0].startswith(" "): # first date
                    comp_parts[0] = comp_parts[0][1:]
                if comp_parts[1].startswith(" "): # second date
                    comp_parts[1] = comp_parts[1][1:]

                # some months are missing from the first one
                if(len(comp_parts[0]) <= 2):
                    month_start = comp_parts[1].find(" ")
                    comp_parts[0] += comp_parts[1][month_start:]

                competition_start = date_from_edition_date_str(comp_parts[0], year)
                competition_end = date_from_edition_date_str(comp_parts[1], year)

            if(id == 63): # paris
                start_date = date(2024, 7, 26)
                end_date = date(2024, 8, 11)
                competition_start = date(2024, 7, 24)
                competition_end = end_date

            # Milano-Cortina has dates in file

            games[id] = Edition(id, edition, row[2], year, row[4], row[5], sys.intern(row[6]), start_date, end_date, competition_start, competition_end, is_held)

    return games

def edition_start_end_to_str(date: Optional[date]) -> str:
    if(date == None):
        return ""
    
    return date.strftime("%d-%b-%Y")

def edition_competition_dates_to_str(competition_start: Optional[date], competition_end: Optional[date]) -> str:
    if(competition_start == None):
        return ""
    
    if(competition_end == None):
        return ""
    
    return f"{competition_start.strftime("%d-%b-%Y")} to {competition_end.strftime("%d-%b-%Y")}"

def write_editions_to_file(file_name: str, editions: dict[int, Edition]) -> None:
    with open(file_name, mode="w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["edition", "edition_id", "edition_url", "year", "city", "country_flag_url", "country_noc", "start_date", "end_date", "competition_date", "isHeld"])
        for _, value in editions.items():
            data = [
                value.edition,
                value.id,
                value.edition_url,
                value.year,
                value.city,
                value.country_flag_url,
                value.country_noc,
                edition_start_end_to_str(value.start_date),
                edition_start_end_to_str(value.end_date),
                edition_competition_dates_to_str(value.competition_start, value.competition_end),
                value.is_held if value.is_held != None else ""
            ]
            writer.writerow(data)
        
# editions = load_games_to_dict_from_file("olympics_games.csv")
# write_editions_to_file("games.csv", editions)