# Problem Identification

## 1. Unknown / Wrong / Inconsistent Data
- Some of the **Paris files (athletes, events, medallists, teams)** may contain missing or inconsistent columns compared to the original data.
- **Missing or invalid date of birth** values will make it impossible to calculate the athlete's age → these will be left as `"UNKNOWN"`.
- Duplicate athletes (same name but different NOC) may exist → they will be matched using the combination of name and date of birth.
- **Medal information** may contain missing values for gold, silver, or bronze → these will be treated as 0.
- **Country codes (NOC)** might be missing or inconsistent → missing ones will be replaced with `"UNK"`.

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

## 4. Testing Criteria
- When the prototype (`project.py`) runs successfully, it should create the following five output files:
  - `new_olympic_athlete_bio.csv`
  - `new_olympic_athlete_event_results.csv`
  - `new_olympics_country.csv`
  - `new_olympics_games.csv`
  - `new_medal_tally.csv`
- The “event results” file must include an extra column named **`age`** at the end (values can be empty).
- The `new_medal_tally.csv` must only contain the header row with these exact fields:

## 5. Confirmation of Success
- Running `python runproject.py` locally should print:
