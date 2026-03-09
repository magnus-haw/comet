import json
import csv
from datetime import datetime

def parse_money(value):
    """Converts currency string to a float"""
    return float(value.replace("$", "").replace(",", "").strip())

def parse_date(value):
    """Parses a date string and converts it to YYYY-MM-DD format, handling both two-digit and four-digit years."""
    if not value.strip():
        return None

    # Try parsing with four-digit year first
    for fmt in ("%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(value.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue  # Try the next format if the first fails

    # If neither format works, raise an error
    raise ValueError(f"Date format not recognized: {value}")

def parse_table_to_json(csv_filepath, json_filepath):
    """Parses a CSV table and converts it to a Django loaddata JSON format"""
    data = [];households = {}
    
    with open(csv_filepath, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        headers = next(reader)  # Read the header row
        
        for row in reader:
            full_name, household_type = row[0].rsplit(" ", 1)
            first_name, last_name = full_name.split(" ", 1)

            # Household Processing
            household_name = last_name+' Family'  # Using last name as household name
            if household_name not in households:
                households[household_name] = {
                    "model": "accc.household",
                    "fields": {
                        "name": household_name,
                        "household_type": household_type
                    }
                }
            security_deposit = parse_money(row[1])
            accc_enroll_date = parse_date(row[2])
            birth_date = parse_date(row[3])
            expected_move_up_date = parse_date(row[6])
            notes = row[8].strip() if row[8] else ""
            current_room = row[9].strip()

            child_entry = {
                "model": "accc.child",
                "fields": {
                    "first_name": first_name,
                    "last_name": last_name,
                    "birth_date": birth_date,
                    "household": [household_name], # Using natural key
                    "security_deposit": security_deposit,
                    "accc_enroll_date": accc_enroll_date,
                    "expected_move_up_date": expected_move_up_date,
                    "notes": notes,
                    "room": [current_room],  # Using natural key
                }
            }

            data.append(child_entry)

    # Combine households and children into one dataset
    data = list(households.values()) + data

    with open(json_filepath, "w", encoding="utf-8") as jsonfile:
        json.dump(data, jsonfile, indent=4)

    print(f"JSON data successfully written to {json_filepath}")

# Example usage:
csv_file = "/home/magnus/Desktop/ACCC/volunteer_hrs/comet/accc/children_table.csv"
json_file = "children_data.json"
parse_table_to_json(csv_file, json_file)
