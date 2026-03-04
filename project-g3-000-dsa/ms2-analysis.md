# MS2 Analysis

## 1. Assumptions and Decisions

### Data Harmonization

This project integrates legacy Olympic datasets with newly provided Paris 2024 datasets. We assumed that the structural differences between the two sources require explicit column mapping and normalization. Paris files use modern formats (e.g., full ISO birthdates, explicit medal types, different NOC naming), while legacy data follows older formatting practices. To maintain consistency, all Paris data is transformed into the legacy schema before merging.

### Athlete Identification

Athletes in the Paris dataset are uniquely identified by the `code` field. We assumed this field corresponds to the legacy `athlete_id` field. If a Paris athlete's ID already exists in legacy data, we treat it as a duplicate and do not re‑insert it.

### Missing or Inconsistent Data

* If a Paris NOC does not appear in the legacy `olympics_country.csv`, it is appended.
* If birthdates cannot be parsed or result in invalid ages (negative or >120), age is recorded as `UNKNOWN`.
* Medallists with `is_medallist != True` are ignored.

### Edition Identification for Paris

We assumed that Paris 2024 corresponds to edition year "2024". If no matching edition is present, we default to:

* `edition_id = 63`
* `edition = "2024 Summer Olympics"`

This ensures downstream processes remain functional.

---

## 2. Data Structure Description

### Dictionaries for Indexing (Primary Data Structure)

The program uses Python dictionaries extensively for O(1) average time lookups.

**Athlete Index**

```
athletes[athlete_id] = { "born": ..., "country_noc": ... }
```

Purpose: Fast retrieval of DOB and NOC while computing age or counting distinct athletes.

**Games Index**

```
games[edition_id] = { "year": ..., "edition": ... }
```

Purpose: Immediate mapping from edition to year for age calculations.

**Country Map**

```
country_map[noc] = country_name
```

Purpose: Used in medal tally output for readable country names.

### Lists for Dataset Storage

All CSV files are stored in list‑of‑lists format after being read. This structure is simple, lightweight, and compatible with the legacy grading scripts.

### Sets for Distinct Athlete Counting

In medal tally computation:

```
entry["athletes"] = set()
```

This ensures accurate tracking of unique athletes per NOC per edition.

### Rationale for Choices

* **Dictionaries** provide O(1) access and allow efficient merging of large datasets.
* **Lists** preserve row order and CSV compatibility.
* **Sets** prevent duplicates without extra overhead.
* Avoided pandas due to assignment restrictions and performance overhead.

---

## 3. General Description of Data Processing

### Step 1 — Load Legacy and Paris Datasets

All CSV files are read into list‑based structures. Paris files are not directly compatible and require transformation.

### Step 2 — Extend Countries with Paris NOCs

The program inserts missing Paris NOCs into the existing country file. This prevents lookup errors during medal tally aggregation.

### Step 3 — Extend Athlete Bio with Paris Athletes

Each Paris athlete row is mapped into legacy schema fields:

* `code → athlete_id`
* `birth_date → born`
* `country_code → noc`

Rows with duplicate athlete IDs are skipped.

### Step 4 — Append Paris Medallist Results

Paris medallist rows are normalized into legacy event‑results schema. New `result_id` values are generated to ensure uniqueness.

### Step 5 — Age Computation

The system unifies two major date formats:

* Legacy: `04-Apr-49`
* Paris: `2000-01-25`

Using `_parse_birth_year()`, the birth year is extracted and validated, and age is calculated using:

```
age = games_year - birth_year
```

Invalid cases become `UNKNOWN`.

### Step 6 — Medal Tally Aggregation

Grouped by `(edition_id, noc)` using dictionaries. Each group tracks:

* number of distinct athletes
* gold/silver/bronze counts
* total medal count

### Step 7 — Output New Files

All new merged datasets are written as:

* `new_olympic_athlete_bio.csv`
* `new_olympic_athlete_event_results.csv`
* `new_olympics_country.csv`
* `new_medal_tally.csv`

---

## 4. Runtime Analysis (Using n, a, p, e, m)

The following variables represent dataset sizes:

* `n` = number of legacy event results
* `a` = number of legacy athlete bio records
* `p` = number of Paris athlete records
* `e` = number of Paris event (medallist) records
* `m` = number of Paris NOC records

### 4.1 Runtime to Clean All Data

Cleaning involves parsing birth years and standardizing fields. Each row is processed once.

```
O(n + a)
```

Birthdate parsing is constant‑time.

### 4.2 Runtime to Add Paris Data to Legacy Records

* Extending bio data: `O(p)`
* Extending NOCs: `O(m)`
* Adding medallist rows: `O(e)`

Total:

```
O(p + m + e)
```

Because dictionary membership checks are O(1).

### 4.3 Runtime to Generate Medal Results

We perform a single pass over the combined results data, whose size is:

```
R = n + e
```

Each row triggers constant‑time updates to tally dictionaries and sets.

```
O(n + e)
```

### Overall Runtime Summary

Combining all phases:

```
O((n + a) + (p + m + e) + (n + e))
= O(n + a + p + m + e)
```

This matches the linear‑time expectation for file‑processing applications.

### Practical Execution

Measured runtime (local machine): ~4 seconds.
This satisfies Level 4 of the timing rubric (≤ 9 seconds).

---

## 5. Performance Considerations

* All merges use dictionary‑based indexing to avoid repeated linear scans.
* Only a single pass is made through large datasets.
* No external libraries are used; built‑in CSV functions minimize overhead.
* Parsed data is reused through in‑memory structures to avoid re‑reading files.

---

## 6. Conclusion

The MS2 application successfully merges heterogeneous Olympic datasets, resolves schema mismatches, computes athlete ages reliably, integrates Paris 2024 medallist data, and generates medal tallies in linear time. The choice of dictionaries, sets, and list‑based CSV structures ensures efficient performance and compatibility with assignment requirements.
