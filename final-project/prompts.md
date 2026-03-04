# Prompts log

This file logs the tool/prompts you used and the results.  A small note on whether it was successful, choices you made and what was used.

## Celal Alyaprak
| Date | Tool / Source | Prompt / Query (verbatim) | Purpose | What Was Kept | Files Impacted |
|------|----------------|---------------------------|----------|----------------|----------------|
| 2025-10-12 | ChatGPT | “Write a Milestone 1 prototype that generates all 5 CSVs and adds an empty 'age' column.” | Build working prototype | `add_empty_age_column`, `create_medal_tally_file` | `project.py` |
| 2025-10-12 | ChatGPT | “Create an MS1 Problem Identification section based on Paris datasets (athletes, events, medallists, teams, nocs).” | Problem ID writing | Organization and handling policies | `ms1_prob_id.md` |
| 2025-11-24 | ChatGPT       | “I need a function to calculate athlete ages from both original DOB formats (‘04-Apr-49’) and Paris format (‘2000-01-25’). Generate a robust parsing function.” | Create a universal age parser    | `_parse_birth_year()` logic, century-handling & mixed formats support | `project.py`      |
| 2025-11-24 | ChatGPT       | “Extend the existing event results to include an 'age' column based on athlete DOB and games year. Use my current build_event_results_with_age function.”       | Complete age integration         | Final version of `build_event_results_with_age()`                     | `project.py`      |
| 2025-11-25 | Claude      | “Convert Paris athletes.csv rows into olympic_athlete_bio.csv format. Columns: athlete_id, name, sex, born, height, weight, country, noc.”                      | Paris athlete merge logic        | Mapping rules + extended bio generation                               | `project.py`      |
| 2025-11-25 | Claude       | “How do I add Paris medallists into olympic_athlete_event_results format while generating new result_id, pos, and medal fields?”                                | Integrate Paris medallists       | Core logic of `add_paris_medallists_to_event_results()`               | `project.py`      |
| 2025-11-25 | ChatGPT       | “Some Paris NOCs don’t exist in olympics_country.csv. Write logic to merge and append missing NOCs safely.”                                                     | Expand countries table           | `extend_countries_with_paris_nocs()` mapping behavior                 | `project.py`      |
| 2025-11-26 | ChatGPT       | “Help me build medal tally aggregation using dictionary grouping by (edition_id, noc). Count distinct athletes + medals.”                                       | Build correct tally calculations | Final grouping logic for `build_medal_tally()`                        | `project.py`      |
| 2025-11-27 | Google Search | “Python csv merging two datasets by column index efficiently”                                                                                                   | Research merging strategy        | Idea to avoid pandas; confirmed dictionary indexing approach          | `project.py`      |
| 2025-11-27 | ChatGPT       | “Write a clean summary of runtime considerations for MS2: cleaning, merging Paris data, and generating medal results using n, a, p, e, m variables.”            | ms2-analysis.md runtime section  | Explanation of big-O and runtime reasoning                            | `ms2-analysis.md` |

## Celal Alyaprak — AI Prompt / Resources Log (MS2)

| Tool / Source | Prompt (verbatim) | Result Summary | How I Used It | Alterations / Fixes |
|----------------|--------------------|----------------|----------------|----------------------|
| Google Search | “python handling csv files without pandas performance considerations” | Found several articles explaining why csv.reader and basic lists/dicts are faster and more memory-efficient for large datasets than pandas. | Confirmed that our project should remain fully csv-based, respecting assignment rules and performance limits. | No direct code used; applied general best practices. |
| StackOverflow | “how to safely merge datasets with different column names in python” | Multiple answers suggested designing explicit mapping rules instead of automated merging. | Used ideas to plan the Paris → legacy field mapping (code → athlete_id, birth_date → born, etc.). | Designed custom mapping logic; nothing copied. |
| claude | “What’s a clean strategy to normalize two different date formats in Python without datetime?” | Suggested splitting strings, checking numeric patterns, and creating a fallback parser. | Used this guidance to build `_parse_birth_year`, supporting both ISO dates and legacy DD-MMM-YY formats. | Completely rewrote logic to match our datasets; added validation (age <0 or >120 → UNKNOWN). |
| StackOverflow | “python extract only the year from mixed-format date strings” | Recommended extracting only the digits for year detection instead of full date parsing. | Used the concept to simplify legacy date parsing for uniform age computation. | Added logic for distinguishing between YY and YYYY formats. |
| claude | “When generating unique IDs for merged CSV rows, what is a simple technique?” | Suggested combining stable fields (e.g., athlete code + medal code) to generate deterministic IDs. | Adopted this idea to create `PARIS-{athlete_code}-{medal_code}` result_id values. | Added prefix, ensured uniqueness, validated against legacy schema. |
| YouTube (Python CSV Tutorial) | “python csv data cleaning tutorial” | Video covered structured CSV workflows and sequential preprocessing. | Influenced the design of the pipeline inside `main()` (load → extend → merge → compute → output). | Adapted structure to fit required file outputs. |
| claude | “How to design a clean dictionary-based grouping approach for medal counting?” | Described using tuple keys and sets to group results efficiently. | Used concept when implementing `build_medal_tally` with `(edition_id, noc)` as keys. | Expanded functionality: added total medal count, unique athlete set, and country name mapping. |
| claude | “Can you review my runtime analysis idea and tell me if it’s linear?” | Confirmed linear time complexity of single-pass file operations with dictionary lookups. | Used confirmation to finalize runtime section in ms2-analysis.md. | Rewrote results using assignment variables (n, a, p, e, m). |
| Claude | “Help me outline a 2-minute reflection script for a data-cleaning project.” | Produced a suggested structure with intro, contributions, challenges, and learnings. | Used structure to prepare my final recorded script. | Shortened content and personalized based on my real work. |




## Gabriel Khan-Figueroa 128094240

|AI tool name|prompt | result | alterations |
|---|---|---|---|
| Google search with AI result | python csv to object  | `reader = csv.DictReader(csvfile)` `person = Person(row['Name'], row['Age'], row['City'])` | `csv_reader = csv.DictReader(file)` `athlete = ParisAthlete(row["country"], row["country_long"], row["nationality"], row["nationality_long"])` |
| Google search with AI result | python calculate age between two dates  | `if (reference_date.month, reference_date.day) < (birth_date.month, birth_date.day):` | `if (date.month, date.day) < (self.id.born.month, self.id.born.day):` |
| Claude | In the file conversion.md are two lists containing all the unique olympic event names found in two different datasets. These are from olympic_athlete_event_results.csv, and paris/medallists.csv. I need a way to convert the event name found in medallists.csv to the old format. Write to a python file a conversion function, as well as any necessary global variables setup. Modify the conversion.py file, which currently only contains a function stub. | conversion.py | As is |
| Claude | In conversion.py, add another function to check if an event name is a team sport or not. The data is found in olympic_athlete_event_results.csv | conversion.py | As is |
| Claude | `ModuleNotFoundError: No module named 'athlete'` error when running runproject.py on github actions | Move files to root | I manually moved files |
| Claude | Missing many paris entries compared to files in the results | `load_paris_athlete_events` | As is |
| Claude | Add position data to missing fields | `load_new_medallists` position logic | As is |
| Claude | Conversions in conversion.py do not properly handle team sports | modified team sports entries | As is |
| Claude | Identify differences between the paris tallies and results compared to publicly known data. Are the paris csv files accurate to existing public records? (segmented) | tally.py sport differentiation isn't present, conversion.py missing conversions | team_key, equestrian, dinghy, relay only athlete |
| Claude | Analyze country and athlete names being formatted or named incorrectly | `smart_title_name` | As is |
| Claude | I think unicode characters are not being handled properly. Please analyze the new_*.csv outputs compared to the input files | TURKISH LETTER PROBLEMATIC (also russian after hyphen). Lots of extra handling in `smart_title_name`. Apostraphe issue fix. | Performance tuning for `smart_title_name`. |
| Claude | Double check if all athlete names are formatted correctly, and other data cleaning issues | Mc/Mac beginning of name `_title_case_part` | As is |
| Claude | Sort countries for formatted output in country.py | sorted countries | As is |
| Claude | Check athlete names again very carefully. Any differences between old and new files should be caught. | German von, and others | `athlete.py` _NAME_PARTICLES |
| Claude | Check if the athletes ages in new_olympic_athlete_event_results.csv are accurate to real data | Angela Ruiz should have been 18 for the Paris 2024, but age column says 17 | Overhaul age calculation logic |

## Roman Harnastaeu 175874239

| Date | Tool / Source | Prompt / Query (verbatim) | Purpose | What Was Kept | Files Impacted |
|------|----------------|---------------------------|----------|----------------|----------------|
| 2025-10-12 | GitHub Copilot | "Generate a markdown table template for AI prompt tracking." | Formatting and table layout | Table structure | `prompts.md` |
| 2025-11-24 | ChatGPT | "How do I parse two different date formats in Python: 'DD-MMM-YY' and 'YYYY-MM-DD'? Need to handle two-digit year ambiguity." | Research date parsing approaches | Century determination logic (00-24 → 2000s, 25-99 → 1900s) | `project.py` |
| 2025-11-24 | GitHub Copilot | "Best practice for handling invalid age values when birth_year - games_year is negative or > 120?" | Age validation edge cases | Return "UNKNOWN" for invalid ranges, added boundary checks | `project.py` |
| 2025-11-24 | Stack Overflow | "Python csv module reading large files efficiently" | Performance optimization research | Kept built-in csv.reader() for memory efficiency | `project.py` |
| 2025-11-24 | ChatGPT | "Write a test function that verifies _parse_birth_year returns correct year from '04-Apr-49' and '2000-01-25' formats." | Unit testing structure | Test case template for birth year parsing validation | `validate_age_calculation.py` |
| 2025-11-24 | GitHub Copilot | "How to count statistics from CSV: total rows, valid vs unknown values, calculate average for numeric column?" | Output metrics calculation | Statistics aggregation logic for validation report | `validate_age_calculation.py` |
| 2025-11-24 | ChatGPT | "Python UnicodeEncodeError 'charmap' codec on Windows console. How to fix print statements?" | Debug encoding issue | Removed non-ASCII characters from output | `project.py` |
