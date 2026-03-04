import csv
import os
import re
import sys

# Add src directory to path before importing
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "src"))
if os.path.exists(src_path):
    sys.path.insert(0, src_path)

from athlete import load_old_athletes_to_dict_from_file, load_unique_paris_athletes_from_file, write_athletes_to_file
from country import loadCountriesToGlobalDictFromFile, loadParisCountries, write_countries_to_file
from edition import load_games_to_dict_from_file, write_editions_to_file
from results import load_new_medallists, load_old_event_results_from_file, load_paris_athlete_events, write_results_to_file
from tally import tally_medals, write_tally_to_file

def format_paris_name(paris_name):
    """
    Convert Paris name format "LASTNAME Firstname" to "Firstname Lastname".
    Examples:
      "ALEKSANYAN Artur" -> "Artur Aleksanyan"
      "McKENZIE Ashley" -> "Ashley McKenzie"
      "van AERT Wout" -> "Wout van Aert"
    """
    if not paris_name or not paris_name.strip():
        return ""
    
    parts = paris_name.strip().split()
    if len(parts) < 2:
        return paris_name.strip().title()
    
    def is_lastname_part(part):
        uppercase_count = sum(1 for c in part if c.isupper())
        if uppercase_count >= 2:
            return True
        if part.isupper():
            return True
        if part.lower() in ['van', 'de', 'el', 'la', 'le', 'del', 'di', 'da', 'dos', 'das']:
            return True
        return False
    
    lastname_parts = []
    firstname_parts = []
    found_firstname = False
    
    for part in parts:
        if not found_firstname and is_lastname_part(part):
            if part.lower() in ['van', 'de', 'el', 'la', 'le', 'del', 'di', 'da', 'dos', 'das']:
                lastname_parts.append(part.lower())
            else:
                lastname_parts.append(part.title())
        else:
            found_firstname = True
            firstname_parts.append(part)
    
    if not firstname_parts:
        if len(lastname_parts) >= 2:
            return lastname_parts[-1] + " " + " ".join(lastname_parts[:-1])
        return paris_name.strip()
    
    lastname = " ".join(lastname_parts)
    firstname = " ".join(firstname_parts)
    
    return firstname + " " + lastname if lastname else firstname


# --- Genel CSV yardımcıları ---

def read_csv_file(file_name):
    data_set = []
    with open(file_name, mode="r", encoding="utf-8-sig") as file:
        reader = csv.reader(file)
        for row in reader:
            data_set.append(row)
    return data_set


def write_csv_file(file_name, data_set):
    with open(file_name, mode="w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        for row in data_set:
            writer.writerow(row)


# --- Index yapıları (sözlükler) ---

def build_athlete_index(bio_data):
    """
    athlete_id -> { "born": ..., "country_noc": ... }
    """
    header = bio_data[0]
    idx_id = header.index("athlete_id")
    idx_born = header.index("born")
    idx_country_noc = header.index("country_noc")

    athletes = {}
    for row in bio_data[1:]:
        athlete_id = row[idx_id]
        athletes[athlete_id] = {
            "born": row[idx_born],
            "country_noc": row[idx_country_noc],
        }
    return athletes


def build_games_index(games_data):
    """
    edition_id -> { "year": ..., "edition": ..., "start_date": ... }
    """
    header = games_data[0]
    idx_edition_id = header.index("edition_id")
    idx_year = header.index("year")
    idx_edition = header.index("edition")
    idx_start_date = header.index("start_date")

    games = {}
    for row in games_data[1:]:
        edition_id = row[idx_edition_id]
        games[edition_id] = {
            "year": row[idx_year],
            "edition": row[idx_edition],
            "start_date": row[idx_start_date],
        }
    return games


def build_country_index(country_data):
    """
    NOC -> country adı
    """
    header = country_data[0]
    idx_noc = header.index("noc")
    idx_country = header.index("country")

    mapping = {}
    for row in country_data[1:]:
        noc = row[idx_noc]
        country = row[idx_country]
        mapping[noc] = country
    return mapping


# --- Paris verisi ile ülke listesini genişlet ---

def extend_countries_with_paris_nocs(country_data, paris_nocs_data):
    """
    paris/nocs.csv içindeki yeni NOC'ları ülke listesine ekler.
    """
    header = country_data[0]
    idx_noc = header.index("noc")
    idx_country = header.index("country")

    existing_nocs = {row[idx_noc] for row in country_data[1:]}

    p_header = paris_nocs_data[0]
    p_idx_code = p_header.index("code")
    # 'country_long' varsa onu tercih edelim, yoksa 'country'
    if "country_long" in p_header:
        p_idx_country = p_header.index("country_long")
    else:
        p_idx_country = p_header.index("country")

    new_rows = []
    for row in paris_nocs_data[1:]:
        code = row[p_idx_code]
        if code and code not in existing_nocs:
            country_name = row[p_idx_country]
            new_rows.append([code, country_name])

    all_rows = country_data[1:] + new_rows
    all_rows.sort(key=lambda row: row[idx_country].lower())
    
    return [header] + all_rows


# --- Age hesaplama yardımcıları ---

def _parse_birth_year(born_str):
    """
    born_str:
      - '04-Apr-49' (orijinal dosya)
      - '2000-01-25' (Paris dosyası)
    """
    if not born_str:
        return None
    s = born_str.strip()
    if not s or s.upper() in ("NA", "N/A", "UNKNOWN"):
        return None

    parts = s.split("-")
    if not parts or len(parts) < 2:
        return None
    
    if parts[0].isdigit() and len(parts[0]) == 4:
        try:
            return int(parts[0])
        except ValueError:
            return None

    last = parts[-1]
    digits = "".join(ch for ch in last if ch.isdigit())
    if not digits:
        return None
    try:
        year_value = int(digits)
    except ValueError:
        return None

    if year_value >= 1800:
        return year_value
    elif year_value <= 24:
        return 2000 + year_value
    else:
        return 1900 + year_value


def standardize_birthdate(born_str):
    """
    born_str: '04-Apr-49', '2000-01-25', '9 June 1892', '(1926 or 1927)', etc.
    """
    if not born_str:
        return ""
    s = born_str.strip()
    if not s or s.upper() in ("NA", "N/A", "UNKNOWN"):
        return ""

    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    month_map = {
        'Jan': 'Jan', 'Feb': 'Feb', 'Mar': 'Mar', 'Apr': 'Apr', 'May': 'May', 'Jun': 'Jun',
        'Jul': 'Jul', 'Aug': 'Aug', 'Sep': 'Sep', 'Oct': 'Oct', 'Nov': 'Nov', 'Dec': 'Dec',
        'January': 'Jan', 'February': 'Feb', 'March': 'Mar', 'April': 'Apr',
        'May': 'May', 'June': 'Jun', 'July': 'Jul', 'August': 'Aug',
        'September': 'Sep', 'October': 'Oct', 'November': 'Nov', 'December': 'Dec'
    }
    
    if " or " in s:
        try:
            index = s.find(" or ")
            year = int(s[index - 4:index])
            return f"01-Jan-{year:04d}"
        except (ValueError, IndexError):
            return ""
    
    if "circa" in s:
        try:
            index = s.find("circa ")
            year = int(s[index + 6:index + 10])
            return f"01-Jan-{year:04d}"
        except (ValueError, IndexError):
            return ""
    
    if "c." in s and "c." != s:
        try:
            index = s.find("c. ")
            year = int(s[index + 3:index + 7])
            return f"01-Jan-{year:04d}"
        except (ValueError, IndexError):
            return ""
    
    if "in " in s:
        return ""
    
    if " " in s and "-" not in s:
        parts = s.split(' ')
        if len(parts) == 2:
            month = month_map.get(parts[0])
            if month and parts[1].isdigit():
                year = int(parts[1])
                return f"01-{month}-{year:04d}"
        elif len(parts) >= 3:
            try:
                day = int(parts[0])
                month = month_map.get(parts[1], parts[1])
                year = int(parts[2])
                return f"{day:02d}-{month}-{year:04d}"
            except (ValueError, IndexError):
                try:
                    month = month_map.get(parts[0])
                    if month and parts[1].isdigit():
                        year = int(parts[1])
                        return f"01-{month}-{year:04d}"
                except:
                    pass
        return ""
    
    if "-" not in s and s.isdigit() and len(s) == 4:
        year = int(s)
        return f"01-Jan-{year:04d}"
    
    parts = s.split("-")
    if len(parts) == 2:
        month = month_map.get(parts[0])
        if month and parts[1].isdigit():
            yy = int(parts[1])
            if yy <= 24:
                year = 2000 + yy
            else:
                year = 1900 + yy
            return f"01-{month}-{year:04d}"
        return ""
    
    if not parts or len(parts) < 3:
        return ""
    
    if parts[0].isdigit() and len(parts[0]) == 4:
        try:
            year = int(parts[0])
            month = int(parts[1])
            day = int(parts[2])
            if 1 <= month <= 12 and 1 <= day <= 31:
                return f"{day:02d}-{month_names[month-1]}-{year:04d}"
        except (ValueError, IndexError):
            pass
        return ""
    
    try:
        day = int(parts[0])
        month_str = parts[1]
        year_part = parts[2]
        
        digits = "".join(ch for ch in year_part if ch.isdigit())
        if not digits:
            return ""
        
        yy = int(digits)
        if yy <= 24:
            year = 2000 + yy
        else:
            year = 1900 + yy
        
        return f"{day:02d}-{month_str}-{year:04d}"
    except (ValueError, IndexError):
        return ""


def parse_full_birthdate(born_str):
    """
    """
    from datetime import date
    if not born_str:
        return None
    s = born_str.strip()
    if not s or s.upper() in ("NA", "N/A", "UNKNOWN"):
        return None
    
    month_map = {
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
        'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12,
        'January': 1, 'February': 2, 'March': 3, 'April': 4,
        'May': 5, 'June': 6, 'July': 7, 'August': 8,
        'September': 9, 'October': 10, 'November': 11, 'December': 12
    }
    
    if " or " in s or "circa" in s or "c." in s or "in " in s:
        year = _parse_birth_year(s)
        if year:
            return date(year, 1, 1)
        return None
    
    if " " in s and "-" not in s:
        try:
            parts = s.split(' ')
            day = int(parts[0])
            month = month_map.get(parts[1])
            year = int(parts[2])
            if month and 1 <= day <= 31:
                return date(year, month, day)
        except (ValueError, IndexError):
            pass
        return None
    
    if "-" not in s and s.isdigit() and len(s) == 4:
        year = int(s)
        return date(year, 1, 1)
    
    parts = s.split("-")
    if len(parts) == 3:
        if parts[0].isdigit() and len(parts[0]) == 4:
            try:
                year = int(parts[0])
                month = int(parts[1])
                day = int(parts[2])
                if 1 <= month <= 12 and 1 <= day <= 31:
                    return date(year, month, day)
            except (ValueError, IndexError):
                pass
        else:
            try:
                day = int(parts[0])
                month = month_map.get(parts[1])
                year_part = parts[2]
                digits = "".join(ch for ch in year_part if ch.isdigit())
                if not digits:
                    return None
                yy = int(digits)
                if yy >= 1800:
                    year = yy
                elif yy <= 24:
                    year = 2000 + yy
                else:
                    year = 1900 + yy
                if month and 1 <= day <= 31:
                    return date(year, month, day)
            except (ValueError, IndexError):
                pass
    
    return None


def parse_games_start_date(start_date_str):
    """
    """
    from datetime import date
    if not start_date_str or start_date_str.strip() in ("", "—", "-"):
        return None
    
    s = start_date_str.strip()
    parts = s.split("-")
    if len(parts) == 3:
        try:
            day = int(parts[0])
            month_map = {
                'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
            }
            month = month_map.get(parts[1])
            year = int(parts[2])
            if month and 1 <= day <= 31:
                return date(year, month, day)
        except (ValueError, IndexError):
            pass
    return None


def compute_age(born_str, games_year_str, games_start_date_str=""):
    """
    born_str: orijinal veya Paris doğum tarihi
    games_year_str: '1896', '2024' gibi.
    games_start_date_str: '26-Jul-2024' gibi (opsiyonel)
    Hata olursa veya anlamsızsa "UNKNOWN" döner.
    """
    if not born_str or not games_year_str:
        return "UNKNOWN"
    
    birth_date = parse_full_birthdate(born_str)
    if birth_date is None:
        return "UNKNOWN"

    try:
        games_year = int(str(games_year_str).strip())
    except (TypeError, ValueError):
        return "UNKNOWN"

    age = games_year - birth_date.year
    
    games_start = parse_games_start_date(games_start_date_str)
    if games_start:
        if (games_start.month, games_start.day) < (birth_date.month, birth_date.day):
            age -= 1
    
    if age < 0 or age > 120:
        return "UNKNOWN"
    return str(age)


def fill_athlete_names(results_data, bio_data):
    """
    """
    header = results_data[0]
    idx_athlete = header.index("athlete")
    idx_athlete_id = header.index("athlete_id")
    
    bio_header = bio_data[0]
    bio_idx_id = bio_header.index("athlete_id")
    bio_idx_name = bio_header.index("name")
    
    athlete_names = {}
    for row in bio_data[1:]:
        athlete_id = row[bio_idx_id]
        name = row[bio_idx_name]
        athlete_names[athlete_id] = name
    
    new_rows = [header]
    for row in results_data[1:]:
        new_row = list(row)
        if not new_row[idx_athlete] or new_row[idx_athlete].strip() == "":
            athlete_id = new_row[idx_athlete_id]
            if athlete_id in athlete_names:
                new_row[idx_athlete] = athlete_names[athlete_id]
        new_rows.append(new_row)
    
    return new_rows


def build_event_results_with_age(results_data, athletes, games):
    """
    Event sonuçlarına en sona 'age' sütununu ekler.
    """
    header = results_data[0]
    
    if 'age' in header:
        new_header = header
        idx_age = header.index("age")
    else:
        new_header = header + ["age"]
        idx_age = len(header)

    idx_athlete_id = header.index("athlete_id")
    idx_edition_id = header.index("edition_id")

    new_rows = [new_header]

    for row in results_data[1:]:
        athlete_id = row[idx_athlete_id]
        edition_id = row[idx_edition_id]

        age_value = "UNKNOWN"

        athlete = athletes.get(athlete_id)
        game = games.get(edition_id)

        if athlete is not None and game is not None:
            dob = athlete.get("born", "")
            games_year = game.get("year", "")
            games_start_date = game.get("start_date", "")
            age_value = compute_age(dob, games_year, games_start_date)

        if len(row) > idx_age:
            new_row = list(row)
            new_row[idx_age] = age_value
        else:
            new_row = row + [""] * (idx_age - len(row)) + [age_value]
        
        new_rows.append(new_row)

    return new_rows


# --- Medal tally hesaplama ---

def build_medal_tally(results_with_age, games, country_map):
    """
    new_medal_tally.csv içeriğini üretir.
    Gruplama: (edition_id, country_noc)
    """
    header = results_with_age[0]
    idx_edition_id = header.index("edition_id")
    idx_noc = header.index("country_noc")
    idx_medal = header.index("medal")
    idx_athlete_id = header.index("athlete_id")

    tally = {}

    for row in results_with_age[1:]:
        edition_id = row[idx_edition_id]
        noc = row[idx_noc]
        medal = row[idx_medal].strip() if idx_medal < len(row) else ""
        athlete_id = row[idx_athlete_id]

        if not edition_id or not noc:
            continue

        key = (edition_id, noc)
        if key not in tally:
            edition_info = games.get(edition_id, {})
            edition_str = edition_info.get("edition", "")
            country_name = country_map.get(noc, "")

            tally[key] = {
                "edition": edition_str,
                "edition_id": edition_id,
                "Country": country_name,
                "NOC": noc,
                "athletes": set(),
                "gold": 0,
                "silver": 0,
                "bronze": 0,
            }

        entry = tally[key]

        if athlete_id:
            entry["athletes"].add(athlete_id)

        if medal:
            medal_lower = medal.lower()
            if medal_lower == "gold":
                entry["gold"] += 1
            elif medal_lower == "silver":
                entry["silver"] += 1
            elif medal_lower == "bronze":
                entry["bronze"] += 1

    output = []
    header_out = [
        "edition",
        "edition_id",
        "Country",
        "NOC",
        "number_of_athletes",
        "gold_medal_count",
        "silver_medal_count",
        "bronze_medal_count",
        "total_medals",
    ]
    output.append(header_out)

    for (edition_id, noc), entry in tally.items():
        num_athletes = len(entry["athletes"])
        gold = entry["gold"]
        silver = entry["silver"]
        bronze = entry["bronze"]
        total = gold + silver + bronze

        row = [
            entry["edition"],
            edition_id,
            entry["Country"],
            noc,
            str(num_athletes),
            str(gold),
            str(silver),
            str(bronze),
            str(total),
        ]
        output.append(row)

    return output


# --- Paris verisini ana kayıtlara ekleme ---

def clean_weight_value(weight_str):
    """
    """
    if not weight_str or weight_str.strip() == "0":
        return ""
    
    weight_str = weight_str.strip()
    
    if "-" in weight_str:
        try:
            parts = weight_str.split("-")
            lhs = int(parts[0])
            rhs = int(parts[1])
            return str(int((lhs + rhs) / 2))
        except (ValueError, IndexError):
            return weight_str
    elif ", " in weight_str:
        try:
            parts = weight_str.split(", ")
            lhs = int(parts[0])
            rhs = int(parts[1])
            return str(int((lhs + rhs) / 2))
        except (ValueError, IndexError):
            return weight_str
    elif "," in weight_str and ", " not in weight_str:
        try:
            parts = weight_str.split(",")
            lhs = int(parts[0])
            rhs = int(parts[1])
            return str(int((lhs + rhs) / 2))
        except (ValueError, IndexError):
            return weight_str
    
    return weight_str


def clean_height_value(height_str):
    """
    """
    if not height_str or height_str.strip() == "0":
        return ""
    return height_str.strip()


def parse_games_date(date_str):
    """
    """
    if not date_str or date_str.strip() in ("", "—"):
        return ""
    
    date_str = date_str.strip()
    
    month_map = {
        "January": "Jan", "February": "Feb", "March": "Mar", "April": "Apr",
        "May": "May", "June": "Jun", "July": "Jul", "August": "Aug",
        "September": "Sep", "October": "Oct", "November": "Nov", "December": "Dec"
    }
    
    for full, abbr in month_map.items():
        date_str = date_str.replace(full, abbr)
    
    parts = date_str.split()
    if len(parts) >= 2:
        try:
            day = int(parts[0])
            month = parts[1]
            if len(parts) >= 3 and parts[2].isdigit():
                year = parts[2]
                return f"{day:02d}-{month}-{year}"
            return f"{day:02d}-{month}"
        except (ValueError, IndexError):
            pass
    
    return date_str


def clean_games_dates(games_data):
    """
    """
    header = games_data[0]
    idx_start = header.index("start_date")
    idx_end = header.index("end_date")
    idx_comp = header.index("competition_date")
    idx_edition_id = header.index("edition_id")
    idx_year = header.index("year")
    
    cleaned_rows = [header]
    
    for row in games_data[1:]:
        new_row = list(row)
        year = row[idx_year]
        
        start_date = parse_games_date(row[idx_start])
        if start_date and year and "-" in start_date and len(start_date.split("-")[-1]) < 4:
            start_date = f"{start_date}-{year}"
        new_row[idx_start] = start_date
        
        end_date = parse_games_date(row[idx_end])
        if end_date and year and "-" in end_date and len(end_date.split("-")[-1]) < 4:
            end_date = f"{end_date}-{year}"
        new_row[idx_end] = end_date
        
        comp_date = row[idx_comp]
        if comp_date and comp_date not in ("—", "-"):
            if " – " in comp_date or " - " in comp_date or "–" in comp_date:
                sep = " – " if " – " in comp_date else (" - " if " - " in comp_date else "–")
                parts = comp_date.split(sep)
                if len(parts) == 2:
                    start_str = parts[0].strip()
                    end_str = parts[1].strip()
                    
                    end_comp = parse_games_date(end_str)
                    
                    if start_str.isdigit() and end_comp:
                        day = int(start_str)
                        month = end_comp.split("-")[1] if "-" in end_comp else ""
                        start_comp = f"{day:02d}-{month}" if month else start_str
                    else:
                        start_comp = parse_games_date(start_str)
                    
                    if start_comp and year and "-" in start_comp and len(start_comp.split("-")[-1]) < 4:
                        start_comp = f"{start_comp}-{year}"
                    if end_comp and year and "-" in end_comp and len(end_comp.split("-")[-1]) < 4:
                        end_comp = f"{end_comp}-{year}"
                    
                    new_row[idx_comp] = f"{start_comp} to {end_comp}"
            else:
                parsed = parse_games_date(comp_date)
                if parsed and year and "-" in parsed and len(parsed.split("-")[-1]) < 4:
                    parsed = f"{parsed}-{year}"
                new_row[idx_comp] = parsed
        elif comp_date == "—" or comp_date == "-":
            new_row[idx_comp] = "—"
        
        if row[idx_edition_id] == "63":
            new_row[idx_start] = "26-Jul-2024"
            new_row[idx_end] = "11-Aug-2024"
            new_row[idx_comp] = "24-Jul-2024 to 11-Aug-2024"
        
        cleaned_rows.append(new_row)
    
    return cleaned_rows


def clean_bio_birthdates(bio_data):
    """
    """
    header = bio_data[0]
    idx_born = header.index("born")
    idx_height = header.index("height")
    idx_weight = header.index("weight")
    
    cleaned_rows = [header]
    for row in bio_data[1:]:
        new_row = list(row)
        new_row[idx_born] = standardize_birthdate(row[idx_born])
        new_row[idx_height] = clean_height_value(row[idx_height])
        new_row[idx_weight] = clean_weight_value(row[idx_weight])
        cleaned_rows.append(new_row)
    
    return cleaned_rows


def extend_bio_with_paris_athletes(bio_data, paris_athletes_data):
    """
    paris/athletes.csv satırlarını olympic_athlete_bio formatına çevirip ekler.
    """
    header = bio_data[0]
    idx_id = header.index("athlete_id")
    idx_name_orig = header.index("name")
    idx_born_orig = header.index("born")
    idx_noc_orig = header.index("country_noc")

    existing_athletes = set()
    for row in bio_data[1:]:
        name = row[idx_name_orig].lower().strip()
        noc = row[idx_noc_orig].strip()
        born_str = row[idx_born_orig]
        
        birth_date = parse_full_birthdate(born_str)
        if birth_date:
            key = (name, birth_date, noc)
            existing_athletes.add(key)

    p_header = paris_athletes_data[0]
    idx_code = p_header.index("code")
    idx_name = p_header.index("name")
    idx_gender = p_header.index("gender")
    idx_birth = p_header.index("birth_date")
    idx_height = p_header.index("height")
    idx_weight = p_header.index("weight")
    idx_country = p_header.index("country")
    idx_country_code = p_header.index("country_code")

    new_rows = []

    for row in paris_athletes_data[1:]:
        athlete_id = row[idx_code]
        if not athlete_id:
            continue

        name_raw = row[idx_name]
        name = format_paris_name(name_raw)
        noc = row[idx_country_code]
        born = row[idx_birth]
        
        birth_date = parse_full_birthdate(born)
        if birth_date:
            key = (name.lower().strip(), birth_date, noc.strip())
            if key in existing_athletes:
                continue

        sex = row[idx_gender]
        height = row[idx_height] if row[idx_height] != "0" else ""
        weight = row[idx_weight] if row[idx_weight] != "0" else ""
        country = " " + row[idx_country] if row[idx_country] else ""

        new_row = [
            athlete_id,
            name,
            sex,
            born,
            height,
            weight,
            country,
            noc,
        ]
        new_rows.append(new_row)

    return [header] + bio_data[1:] + new_rows


def extend_bio_with_team_athletes(bio_data, paris_teams_data, paris_athletes_data):
    header = bio_data[0]
    
    p_header = paris_athletes_data[0]
    p_idx_code = p_header.index("code")
    paris_codes = {row[p_idx_code] for row in paris_athletes_data[1:] if row[p_idx_code]}
    
    bio_ids = {row[header.index("athlete_id")] for row in bio_data[1:]}
    
    t_header = paris_teams_data[0]
    t_idx_country_code = t_header.index("country_code")
    t_idx_country = t_header.index("country")
    t_idx_athletes = t_header.index("athletes")
    t_idx_athletes_codes = t_header.index("athletes_codes")
    t_idx_events = t_header.index("events")
    
    new_rows = []
    added_codes = {}
    
    for row in paris_teams_data[1:]:
        noc = row[t_idx_country_code]
        country = row[t_idx_country]
        athletes_str = row[t_idx_athletes]
        codes_str = row[t_idx_athletes_codes]
        event_name = row[t_idx_events]
        
        if not codes_str or codes_str == "[]":
            continue
        
        gender = ""
        if event_name:
            event_lower = event_name.lower()
            if "men's" in event_lower and "women" not in event_lower:
                gender = "Male"
            elif "women" in event_lower:
                gender = "Female"
        
        codes_str = codes_str.strip("[]'\"")
        codes = [c.strip().strip("'\"") for c in codes_str.split(",")]
        
        names = []
        name_matches = re.findall(r"'([^']*)'", athletes_str)
        if name_matches:
            names = name_matches
        
        for i, code in enumerate(codes):
            if not code:
                continue
            if code in paris_codes:
                continue
            if code in bio_ids:
                continue
            if code in added_codes:
                if gender and not added_codes[code]['gender']:
                    added_codes[code]['gender'] = gender
                continue
            
            name_raw = names[i] if i < len(names) else ""
            if not name_raw:
                continue
            
            name = format_paris_name(name_raw)
            added_codes[code] = {
                'name': name,
                'gender': gender,
                'country': country,
                'noc': noc,
            }
    
    for code, data in added_codes.items():
        new_row = [
            code,
            data['name'],
            data['gender'],
            "",
            "",
            "",
            " " + data['country'] if data['country'] else "",
            data['noc'],
        ]
        new_rows.append(new_row)
    
    return [header] + bio_data[1:] + new_rows


def build_paris_to_bio_id_map(bio_data, paris_athletes_data):
    bio_header = bio_data[0]
    idx_bio_id = bio_header.index("athlete_id")
    idx_bio_name = bio_header.index("name")
    idx_bio_noc = bio_header.index("country_noc")
    
    bio_by_name_noc = {}
    for row in bio_data[1:]:
        name = row[idx_bio_name].lower().strip()
        noc = row[idx_bio_noc].strip()
        bio_id = row[idx_bio_id]
        bio_by_name_noc[(name, noc)] = bio_id
    
    p_header = paris_athletes_data[0]
    p_idx_code = p_header.index("code")
    p_idx_name = p_header.index("name")
    p_idx_noc = p_header.index("country_code")
    
    paris_to_bio = {}
    for row in paris_athletes_data[1:]:
        code = row[p_idx_code]
        name = row[p_idx_name].lower().strip()
        noc = row[p_idx_noc].strip()
        
        if (name, noc) in bio_by_name_noc:
            paris_to_bio[code] = bio_by_name_noc[(name, noc)]
        else:
            paris_to_bio[code] = code
    
    return paris_to_bio


def add_paris_teams_to_event_results(results_data, paris_teams_data, paris_athletes_data, paris_medallists_data, edition_id_paris, edition_name_paris, paris_to_bio_id=None):
    """
    """
    header = results_data[0]
    idx_edition = header.index("edition")
    idx_edition_id = header.index("edition_id")
    idx_country_noc = header.index("country_noc")
    idx_sport = header.index("sport")
    idx_event = header.index("event")
    idx_result_id = header.index("result_id")
    idx_athlete = header.index("athlete")
    idx_athlete_id = header.index("athlete_id")
    idx_pos = header.index("pos")
    idx_medal = header.index("medal")
    idx_is_team = header.index("isTeamSport")

    p_header = paris_athletes_data[0]
    p_idx_code = p_header.index("code")
    p_idx_name = p_header.index("name")
    
    athlete_name_map = {}
    for row in paris_athletes_data[1:]:
        code = row[p_idx_code]
        name = format_paris_name(row[p_idx_name])
        if code:
            athlete_name_map[code] = name
    
    m_header = paris_medallists_data[0]
    m_idx_code_athlete = m_header.index("code_athlete")
    m_idx_event = m_header.index("event")
    m_idx_medal_type = m_header.index("medal_type")
    m_idx_code_team = m_header.index("code_team")
    
    from collections import defaultdict
    team_medal_counts = defaultdict(set)
    for row in paris_medallists_data[1:]:
        code_team = row[m_idx_code_team] if m_idx_code_team < len(row) else ""
        if not code_team or not code_team.strip():
            continue
        athlete_code = row[m_idx_code_athlete]
        event = row[m_idx_event]
        medal_type = row[m_idx_medal_type].lower()
        if athlete_code:
            team_medal_counts[(event, medal_type)].add(athlete_code)
    
    medal_map = {}
    for row in paris_medallists_data[1:]:
        code_team = row[m_idx_code_team] if m_idx_code_team < len(row) else ""
        if not code_team or not code_team.strip():
            continue
        athlete_code = row[m_idx_code_athlete]
        event = row[m_idx_event]
        medal_type = row[m_idx_medal_type].lower()
        
        is_tie = len(team_medal_counts[(event, medal_type)]) > 1
        
        if "gold" in medal_type:
            medal = "Gold"
            pos = "=1" if is_tie else "1"
        elif "silver" in medal_type:
            medal = "Silver"
            pos = "=2" if is_tie else "2"
        elif "bronze" in medal_type:
            medal = "Bronze"
            pos = "=3" if is_tie else "3"
        else:
            medal = ""
            pos = ""
        
        medal_map[(athlete_code, event)] = (medal, pos)

    max_result_id = 0
    for row in results_data[1:]:
        try:
            rid = int(row[idx_result_id])
            if rid > max_result_id:
                max_result_id = rid
        except (ValueError, IndexError):
            pass

    new_rows = []
    counter = max_result_id + 1
    added_team_athletes = set()

    t_header = paris_teams_data[0]
    t_idx_country_code = t_header.index("country_code")
    t_idx_discipline = t_header.index("discipline")
    t_idx_events = t_header.index("events")
    t_idx_athletes = t_header.index("athletes")
    t_idx_athletes_codes = t_header.index("athletes_codes")
    
    for row in paris_teams_data[1:]:
        noc = row[t_idx_country_code]
        discipline = row[t_idx_discipline]
        event_name = row[t_idx_events]
        athletes_str = row[t_idx_athletes]
        codes_str = row[t_idx_athletes_codes]
        
        if not codes_str or codes_str == "[]":
            continue
        
        if not event_name or not event_name.strip():
            continue
        
        codes_str = codes_str.strip("[]'\"")
        codes = [c.strip().strip("'\"") for c in codes_str.split(",")]
        
        names_str = athletes_str.strip("[]")
        names = []
        name_matches = re.findall(r"'([^']*)'", athletes_str)
        if name_matches:
            names = name_matches
        else:
            names = [n.strip().strip("'\"") for n in names_str.split(",")]
        while len(names) < len(codes):
            names.append("")
        
        for i, athlete_code in enumerate(codes):
            if not athlete_code:
                continue
            
            dedup_key = (athlete_code, event_name, noc)
            if dedup_key in added_team_athletes:
                continue
            added_team_athletes.add(dedup_key)
            
            athlete_name = format_paris_name(names[i]) if i < len(names) and names[i] else athlete_name_map.get(athlete_code, "")
            
            medal_info = medal_map.get((athlete_code, event_name), ("", ""))
            medal = medal_info[0]
            pos = medal_info[1]
            
            result_id = str(counter)
            counter += 1
            
            new_row = [""] * len(header)
            new_row[idx_edition] = edition_name_paris
            new_row[idx_edition_id] = edition_id_paris
            new_row[idx_country_noc] = noc
            new_row[idx_sport] = discipline
            new_row[idx_event] = event_name
            new_row[idx_result_id] = result_id
            final_athlete_id = athlete_code
            if paris_to_bio_id and athlete_code in paris_to_bio_id:
                final_athlete_id = paris_to_bio_id[athlete_code]
            
            new_row[idx_athlete] = athlete_name
            new_row[idx_athlete_id] = final_athlete_id
            new_row[idx_pos] = pos
            new_row[idx_medal] = medal
            new_row[idx_is_team] = "True"
            
            new_rows.append(new_row)
    
    return [header] + results_data[1:] + new_rows


def add_paris_medallists_to_event_results(results_data, paris_medallists_data, edition_id_paris, edition_name_paris, paris_to_bio_id=None):
    """
    paris/medallists.csv'den, olympic_athlete_event_results formatında satırlar üretir.
    """
    header = results_data[0]
    idx_edition = header.index("edition")
    idx_edition_id = header.index("edition_id")
    idx_country_noc = header.index("country_noc")
    idx_sport = header.index("sport")
    idx_event = header.index("event")
    idx_result_id = header.index("result_id")
    idx_athlete = header.index("athlete")
    idx_athlete_id = header.index("athlete_id")
    idx_pos = header.index("pos")
    idx_medal = header.index("medal")
    idx_is_team = header.index("isTeamSport")

    p_header = paris_medallists_data[0]
    p_idx_country_code = p_header.index("country_code")
    p_idx_name = p_header.index("name")
    p_idx_discipline = p_header.index("discipline")
    p_idx_event = p_header.index("event")
    p_idx_medal_type = p_header.index("medal_type")
    p_idx_medal_code = p_header.index("medal_code")
    p_idx_code_athlete = p_header.index("code_athlete")
    p_idx_code_team = p_header.index("code_team")
    p_idx_is_medallist = p_header.index("is_medallist")

    from collections import defaultdict
    indiv_medal_counts = defaultdict(set)
    for row in paris_medallists_data[1:]:
        code_team = row[p_idx_code_team] if p_idx_code_team < len(row) else ""
        if code_team and code_team.strip():
            continue
        athlete_code = row[p_idx_code_athlete]
        event = row[p_idx_event]
        medal_type = row[p_idx_medal_type].lower()
        if athlete_code:
            indiv_medal_counts[(event, medal_type)].add(athlete_code)

    max_result_id = 0
    for row in results_data[1:]:
        try:
            rid = int(row[idx_result_id])
            if rid > max_result_id:
                max_result_id = rid
        except (ValueError, IndexError):
            pass

    new_rows = []
    counter = max_result_id + 1

    for row in paris_medallists_data[1:]:
        code_team = row[p_idx_code_team] if p_idx_code_team < len(row) else ""
        if code_team and code_team.strip():
            continue

        noc = row[p_idx_country_code]
        name = format_paris_name(row[p_idx_name])
        discipline = row[p_idx_discipline]
        event = row[p_idx_event]
        medal_type = row[p_idx_medal_type]
        athlete_code = row[p_idx_code_athlete]

        medal_type_lower = medal_type.lower()
        is_tie = len(indiv_medal_counts[(event, medal_type_lower)]) > 1
        
        if "gold" in medal_type_lower:
            medal_simple = "Gold"
            pos = "=1" if is_tie else "1"
        elif "silver" in medal_type_lower:
            medal_simple = "Silver"
            pos = "=2" if is_tie else "2"
        elif "bronze" in medal_type_lower:
            medal_simple = "Bronze"
            pos = "=3" if is_tie else "3"
        else:
            medal_simple = ""
            pos = ""

        result_id = str(counter)
        counter += 1

        new_row = [""] * len(header)
        new_row[idx_edition] = edition_name_paris
        new_row[idx_edition_id] = edition_id_paris
        new_row[idx_country_noc] = noc
        new_row[idx_sport] = discipline
        new_row[idx_event] = event
        final_athlete_id = athlete_code
        if paris_to_bio_id and athlete_code in paris_to_bio_id:
            final_athlete_id = paris_to_bio_id[athlete_code]
        
        new_row[idx_result_id] = result_id
        new_row[idx_athlete] = name
        new_row[idx_athlete_id] = final_athlete_id
        new_row[idx_pos] = pos
        new_row[idx_medal] = medal_simple
        new_row[idx_is_team] = "False"

        new_rows.append(new_row)

    return [header] + results_data[1:] + new_rows


def add_paris_from_athletes_events(results_data, paris_athletes_data, paris_medallists_data, paris_teams_data, edition_id_paris, edition_name_paris, paris_to_bio_id=None):
    header = results_data[0]
    idx_edition = header.index("edition")
    idx_edition_id = header.index("edition_id")
    idx_country_noc = header.index("country_noc")
    idx_sport = header.index("sport")
    idx_event = header.index("event")
    idx_result_id = header.index("result_id")
    idx_athlete = header.index("athlete")
    idx_athlete_id = header.index("athlete_id")
    idx_pos = header.index("pos")
    idx_medal = header.index("medal")
    idx_is_team = header.index("isTeamSport")

    m_header = paris_medallists_data[0]
    m_idx_code_athlete = m_header.index("code_athlete")
    m_idx_event = m_header.index("event")
    m_idx_medal_type = m_header.index("medal_type")
    
    from collections import defaultdict
    medal_counts = defaultdict(set)
    for row in paris_medallists_data[1:]:
        athlete_code = row[m_idx_code_athlete]
        event = row[m_idx_event]
        medal_type = row[m_idx_medal_type].lower()
        if athlete_code:
            medal_counts[(event, medal_type)].add(athlete_code)
    
    medal_map = {}
    for row in paris_medallists_data[1:]:
        athlete_code = row[m_idx_code_athlete]
        event = row[m_idx_event]
        medal_type = row[m_idx_medal_type].lower()
        
        is_tie = len(medal_counts[(event, medal_type)]) > 1
        
        if "gold" in medal_type:
            medal = "Gold"
            pos = "=1" if is_tie else "1"
        elif "silver" in medal_type:
            medal = "Silver"
            pos = "=2" if is_tie else "2"
        elif "bronze" in medal_type:
            medal = "Bronze"
            pos = "=3" if is_tie else "3"
        else:
            medal = ""
            pos = ""
        
        medal_map[(athlete_code, event)] = (medal, pos)
    
    t_header = paris_teams_data[0]
    t_idx_events = t_header.index("events")
    
    team_events = set()
    for row in paris_teams_data[1:]:
        event = row[t_idx_events]
        if event:
            team_events.add(event)

    max_result_id = 0
    for row in results_data[1:]:
        try:
            rid = int(row[idx_result_id])
            if rid > max_result_id:
                max_result_id = rid
        except (ValueError, IndexError):
            pass

    new_rows = []
    counter = max_result_id + 1
    added_entries = set()

    p_header = paris_athletes_data[0]
    p_idx_code = p_header.index("code")
    p_idx_name = p_header.index("name")
    p_idx_country_code = p_header.index("country_code")
    p_idx_disciplines = p_header.index("disciplines")
    p_idx_events = p_header.index("events")
    
    for row in paris_athletes_data[1:]:
        athlete_code = row[p_idx_code]
        if not athlete_code:
            continue
        
        name = format_paris_name(row[p_idx_name])
        noc = row[p_idx_country_code]
        disciplines_str = row[p_idx_disciplines]
        events_str = row[p_idx_events]
        
        if not events_str:
            continue
        
        events_str = events_str.strip("[]")
        event_matches = re.findall(r'"([^"]*)"', row[p_idx_events])
        if not event_matches:
            events = [e.strip().strip("'\"") for e in events_str.split(",")]
        else:
            events = event_matches
        
        disciplines_str = disciplines_str.strip("[]")
        disc_matches = re.findall(r"'([^']*)'", row[p_idx_disciplines])
        if disc_matches:
            discipline = disc_matches[0]
        else:
            discipline = disciplines_str.strip("'\"")
        
        for event in events:
            event = event.strip()
            if not event:
                continue
            
            key = (athlete_code, event)
            if key in added_entries:
                continue
            added_entries.add(key)
            
            medal_info = medal_map.get(key, ("", ""))
            medal = medal_info[0]
            pos = medal_info[1]
            
            is_team = "True" if event in team_events else "False"
            
            final_athlete_id = athlete_code
            if paris_to_bio_id and athlete_code in paris_to_bio_id:
                final_athlete_id = paris_to_bio_id[athlete_code]
            
            result_id = str(counter)
            counter += 1
            
            new_row = [""] * len(header)
            new_row[idx_edition] = edition_name_paris
            new_row[idx_edition_id] = edition_id_paris
            new_row[idx_country_noc] = noc
            new_row[idx_sport] = discipline
            new_row[idx_event] = event
            new_row[idx_result_id] = result_id
            new_row[idx_athlete] = name
            new_row[idx_athlete_id] = final_athlete_id
            new_row[idx_pos] = pos
            new_row[idx_medal] = medal
            new_row[idx_is_team] = is_team
            
            new_rows.append(new_row)
    
    m_idx_discipline = paris_medallists_data[0].index("discipline")
    m_idx_name = paris_medallists_data[0].index("name")
    m_idx_country = paris_medallists_data[0].index("country_code")
    
    for row in paris_medallists_data[1:]:
        athlete_code = row[m_idx_code_athlete]
        event = row[m_idx_event]
        
        key = (athlete_code, event)
        if key in added_entries:
            continue
        added_entries.add(key)
        
        name = format_paris_name(row[m_idx_name])
        noc = row[m_idx_country]
        discipline = row[m_idx_discipline]
        medal_type = row[m_idx_medal_type].lower()
        
        if "gold" in medal_type:
            medal = "Gold"
            pos = "1"
        elif "silver" in medal_type:
            medal = "Silver"
            pos = "2"
        elif "bronze" in medal_type:
            medal = "Bronze"
            pos = "3"
        else:
            medal = ""
            pos = ""
        
        is_team = "True" if event in team_events else "False"
        
        final_athlete_id = athlete_code
        if paris_to_bio_id and athlete_code in paris_to_bio_id:
            final_athlete_id = paris_to_bio_id[athlete_code]
        
        result_id = str(counter)
        counter += 1
        
        new_row = [""] * len(header)
        new_row[idx_edition] = edition_name_paris
        new_row[idx_edition_id] = edition_id_paris
        new_row[idx_country_noc] = noc
        new_row[idx_sport] = discipline
        new_row[idx_event] = event
        new_row[idx_result_id] = result_id
        new_row[idx_athlete] = name
        new_row[idx_athlete_id] = final_athlete_id
        new_row[idx_pos] = pos
        new_row[idx_medal] = medal
        new_row[idx_is_team] = is_team
        
        new_rows.append(new_row)
    
    return [header] + results_data[1:] + new_rows


# --- main() ---

# def main():
#     # Orijinal dosyaları yükle
#     bio_data = read_csv_file("olympic_athlete_bio.csv")
#     results_data = read_csv_file("olympic_athlete_event_results.csv")
#     country_data = read_csv_file("olympics_country.csv")
#     games_data = read_csv_file("olympics_games.csv")

#     # Paris dosyalarını yükle
#     paris_athletes_data = read_csv_file("paris/athletes.csv")
#     paris_medallists_data = read_csv_file("paris/medallists.csv")
#     paris_nocs_data = read_csv_file("paris/nocs.csv")
#     paris_teams_data = read_csv_file("paris/teams.csv")

#     # Ülke listesine Paris NOC'larını ekle
#     country_data_extended = extend_countries_with_paris_nocs(country_data, paris_nocs_data)

#     # Athlete bio'ya Paris atletlerini ekle
#     bio_data_extended = extend_bio_with_paris_athletes(bio_data, paris_athletes_data)
#     bio_data_extended = extend_bio_with_team_athletes(bio_data_extended, paris_teams_data, paris_athletes_data)

#     bio_data_cleaned = clean_bio_birthdates(bio_data_extended)

#     games_data_cleaned = clean_games_dates(games_data)

#     # Index yapıları
#     athletes = build_athlete_index(bio_data_cleaned)
#     games = build_games_index(games_data_cleaned)
#     country_map = build_country_index(country_data_extended)

#     # Paris için edition_id ve edition adını bul (2024 Summer Olympics)
#     paris_edition_id = None
#     paris_edition_name = None
#     header_games = games_data_cleaned[0]
#     idx_ed_name = header_games.index("edition")
#     idx_ed_id = header_games.index("edition_id")
#     idx_year = header_games.index("year")
#     for row in games_data_cleaned[1:]:
#         if row[idx_year] == "2024":
#             paris_edition_id = row[idx_ed_id]
#             paris_edition_name = row[idx_ed_name]
#             break

#     # Güvenlik için default değer
#     if paris_edition_id is None:
#         paris_edition_id = "63"
#         paris_edition_name = "2024 Summer Olympics"

#     paris_to_bio_id = build_paris_to_bio_id_map(bio_data, paris_athletes_data)

#     results_with_paris = add_paris_from_athletes_events(
#         results_data,
#         paris_athletes_data,
#         paris_medallists_data,
#         paris_teams_data,
#         paris_edition_id,
#         paris_edition_name,
#         paris_to_bio_id,
#     )

#     results_with_age = build_event_results_with_age(results_with_paris, athletes, games)

#     # Medal tally üret
#     medal_tally_rows = build_medal_tally(results_with_age, games, country_map)

#     # Çıktı dosyalarını yaz
#     write_csv_file("new_olympic_athlete_bio.csv", bio_data_cleaned)
#     write_csv_file("new_olympic_athlete_event_results.csv", results_with_age)
#     write_csv_file("new_olympics_country.csv", country_data_extended)
#     write_csv_file("new_olympics_games.csv", games_data_cleaned)
#     write_csv_file("new_medal_tally.csv", medal_tally_rows)

#     print(" Milestone 2 core with Paris data complete — age + medal tally generated.")

def main():
    countries = loadCountriesToGlobalDictFromFile("olympics_country.csv")
    loadParisCountries("paris/nocs.csv", countries)

    editions = load_games_to_dict_from_file("olympics_games.csv")

    athletes = load_old_athletes_to_dict_from_file("olympic_athlete_bio.csv", countries)
    athletes = load_unique_paris_athletes_from_file("paris/athletes.csv", athletes, countries)
    results = load_old_event_results_from_file("olympic_athlete_event_results.csv",  athletes, editions)
    results = load_new_medallists("paris/medallists.csv", results, athletes, editions)
    results = load_paris_athlete_events("paris/medallists.csv", results, athletes, editions)

    tallies = tally_medals(editions, results)

    write_editions_to_file("new_olympics_games.csv", editions)
    write_countries_to_file("new_olympics_country.csv", countries)
    write_athletes_to_file("new_olympic_athlete_bio.csv", athletes, countries)
    write_results_to_file("new_olympic_athlete_event_results.csv", results, editions, athletes)
    write_tally_to_file("new_medal_tally.csv", tallies, editions, countries)
