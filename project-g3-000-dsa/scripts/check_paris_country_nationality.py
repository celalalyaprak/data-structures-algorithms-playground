import csv

class ParisAthlete:
    def __init__(self, country, country_long, nationality, nationality_long):
        self.country = country
        self.country_long = country_long
        self.nationality = nationality
        self.nationality_long = nationality_long

def read_csv_file(file_name):
    data_set = []
    with open(file_name, mode='r', encoding="utf-8-sig") as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            athlete = ParisAthlete(row["country"], row["country_long"], row["nationality"], row["nationality_long"])
            data_set.append(athlete)
    return data_set

data = read_csv_file("../paris/athletes.csv")
for entry in data:
    if entry.country != entry.nationality:
        print(f"Found mismatch. {entry.country} != {entry.nationality}")
    if entry.country_long != entry.nationality_long:
        print(f"Found mismatch. {entry.country_long} != {entry.nationality_long}")
