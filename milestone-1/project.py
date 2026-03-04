# Feel free to add additional python files to this project and import
# them in this file. However, do not change the name of this file
# Avoid the names ms1check.py and ms2check.py as those file names
# are reserved for the autograder

# To run your project use:
#     python runproject.py

import csv


# This function reads a csv file and return a list of lists
def read_csv_file(file_name):
    data_set = []
    with open(file_name, mode='r', encoding="utf-8-sig") as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            data_set.append(row)
    return data_set


# This function writes out a list of lists to a csv file
def write_csv_file(file_name, data_set):
    with open(file_name, mode='w', newline='', encoding="utf-8-sig") as file:
        csv_writer = csv.writer(file)
        for row in data_set:
            csv_writer.writerow(row)


def add_empty_age_column(file_in, file_out):
    """
    Reads the event results CSV file and creates a new file
    with an empty 'age' column added at the end.
    """
    with open(file_in, mode='r', encoding="utf-8-sig") as fin, open(file_out, mode='w', newline='', encoding="utf-8-sig") as fout:
        reader = csv.reader(fin)
        writer = csv.writer(fout)

        # header
        header = next(reader)
        header.append("age")
        writer.writerow(header)

        # data rows
        for row in reader:
            row.append("")  # boş sütun
            writer.writerow(row)


def create_medal_tally_file(file_out):
    """
    Creates a new CSV file with only the header for medal tally.
    """
    header = [
        "edition", "edition_id", "Country", "NOC",
        "number_of_athletes", "gold_medal_count",
        "silver_medal_count", "bronze_medal_count", "total_medals"
    ]
    with open(file_out, mode='w', newline='', encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(header)


# Main runner (called automatically by runproject.py)
def main():
    # 1️⃣ new_olympic_athlete_bio.csv
    bio_data = read_csv_file("olympic_athlete_bio.csv")
    write_csv_file("new_olympic_athlete_bio.csv", bio_data)

    # 2️⃣ new_olympic_athlete_event_results.csv (add age column)
    add_empty_age_column("olympic_athlete_event_results.csv", "new_olympic_athlete_event_results.csv")

    # 3️⃣ new_olympics_country.csv
    country_data = read_csv_file("olympics_country.csv")
    write_csv_file("new_olympics_country.csv", country_data)

    # 4️⃣ new_olympics_games.csv
    games_data = read_csv_file("olympics_games.csv")
    write_csv_file("new_olympics_games.csv", games_data)

    # 5️⃣ new_medal_tally.csv
    create_medal_tally_file("new_medal_tally.csv")

    print("✅ Milestone 1 prototype complete — 5 CSV files created.")


if __name__ == "__main__":
    main()
