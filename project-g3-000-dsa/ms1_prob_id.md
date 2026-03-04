
# Milestone 1 Problem Identification

## 1. Unknown / Wrong / Inconsistent Data

- Some of the **Paris files (athletes, events, medallists, teams)** may contain missing or inconsistent columns compared to the original data.
- **Missing or invalid date of birth** values will make it impossible to calculate the athlete's age → these will be left as `"UNKNOWN"`.
- Duplicate athletes (same name but different NOC) may exist → they will be matched using the combination of name and date of birth.
- **Medal information** may contain missing values for gold, silver, or bronze → these will be treated as 0.
- **Country codes (NOC)** might be missing or inconsistent → missing ones will be replaced with `"UNK"`.
- Some athletes in the paris data are under a **Refugee** status. While they do have a nationality, they may need to be distinguished from the country's athletes themselves.

## 2. Handling of Wrong / Unknown Data

- Missing values will be replaced with `"UNKNOWN"`.
- Critical missing fields such as `athlete_id` or `edition_id` will be kept but marked as `"needs_review"`.
- Any inconsistent or incorrect NOC codes will be corrected based on the data in `olympics_country.csv`.

## 3. Paris Data Organization

- The `paris/` folder contains five new CSV files from the 2024 Paris Olympics:
  - **athletes.csv** → aligned with `olympic_athlete_bio.csv` (same structure, columns normalized).
  - **events.csv** → aligned with `olympic_athlete_event_results.csv`.
  - **nocs.csv** → mapped to `olympics_country.csv` (country and NOC relationships).
  - **teams.csv** → connected to athlete and event data to identify team memberships.
  - **medallists.csv** → will be used to generate `new_medal_tally.csv`.
- The Paris data will be cleaned, standardized, and merged with the original datasets to maintain consistent structure and schema.

### Athlete Data Differences

An athlete can exist as a dedicated data structure without any medal information.

The normal file `olympic_athlete_bio.csv` contains the fields:

1. athlete_id
2. name
3. sex
4. born
5. height (missing in many instances)
6. weight (missing in many instances)
7. country
8. country_noc

The paris file `athletes.csv` contains the fields:

1. code
2. current
3. name
4. name_short
5. name_tv
6. gender
7. function
8. country_code
9. country
10. country_long
11. nationality
12. nationality_long
13. nationality_code
14. height (0 in many instances)
15. weight (0 in many instances)
16. disciplines
17. events
18. birth_date
19. birth_place
20. birth_country
21. residence_place
22. residence_country

A lot of these fields are not relevant.

### Country and Nationality

The country and nationality fields found in the paris `athletes.csv` file do not always match, for instance with Refugee Olympic Team and Puerto Rico. This is checked with our custom script `scripts/check_paris_country_nationality.py`. To resolve this, we must determine which to use. Nationality may be the right option.

### Birth Dates

The format of the birth dates differs between `olympic_athlete_bio.csv`, as well as the paris data. The `olympic_athlete_bio.csv` uses the format `DD-Mon-YY`, whereas the paris data uses the format `YYYY-MM-DD`. Mon is the month represented in text (ie. October -> Oct).

As such, we need a generic way to turn either format into a consistent format. We can convert the strings found within the csv files into the data type `datetime.date`.

## 4. Testing Criteria / Confirmation of Success

- Running `python runproject.py` locally should create the following five output files:
  - `new_olympic_athlete_bio.csv`
  - `new_olympic_athlete_event_results.csv`
  - `new_olympics_country.csv`
  - `new_olympics_games.csv`
  - `new_medal_tally.csv`
- The “event results” file must include an extra column named **`age`** at the end (values can be empty).
- The `new_medal_tally.csv` must only contain the header row with these exact fields:
