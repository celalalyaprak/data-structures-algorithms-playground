# Prompts log

This file logs the tool/prompts you used and the results.  A small note on whether it was successful, choices you made and what was used.

## Example (can be deleted):

|AI tool name|prompt | result | alterations |
|---|---|---|---|
|gh copilot|what do you use to read in csv files in python| csv module or pandas | rejected pandas as it is not allowed |
|gh copilot|write a function that is passed the name of a csv file and will return the data set of that file| read_csv_file(file_name) | updated to account for utf-8 formatting |

## Celal Alyaprak
| Date | Tool / Source | Prompt / Query (verbatim) | Purpose | What Was Kept | Files Impacted |
|------|----------------|---------------------------|----------|----------------|----------------|
| 2025-10-12 | ChatGPT | “Write a Milestone 1 prototype that generates all 5 CSVs and adds an empty 'age' column.” | Build working prototype | `add_empty_age_column`, `create_medal_tally_file` | `project.py` |

---

## Member 2
| Date | Tool / Source | Prompt / Query (verbatim) | Purpose | What Was Kept | Files Impacted |
|------|----------------|---------------------------|----------|----------------|----------------|
| 2025-10-12 | ChatGPT | “Create an MS1 Problem Identification section based on Paris datasets (athletes, events, medallists, teams, nocs).” | Problem ID writing | Organization and handling policies | `ms1_prob_id.md` |

---

## Member 3
| Date | Tool / Source | Prompt / Query (verbatim) | Purpose | What Was Kept | Files Impacted |
|------|----------------|---------------------------|----------|----------------|----------------|
| 2025-10-12 | GitHub Copilot | “Generate a markdown table template for AI prompt tracking.” | Formatting and table layout | Table structure | `prompts.md` |