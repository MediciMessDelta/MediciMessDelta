import csv
import json
import os


def load_csv(path):
    """Opens a CSV file and gives back a list of rows.
    Each row is a dictionary, so you can look up a value by
    column name, like row['branch']."""

    if not os.path.exists(path):
        raise FileNotFoundError("CSV file not found: " + path)

    rows = []
    with open(path, newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            rows.append(dict(row))

    return rows


def load_json(path):
    """Same idea as load_csv, but for a JSON file."""

    if not os.path.exists(path):
        raise FileNotFoundError("JSON file not found: " + path)

    with open(path) as file:
        raw_records = json.load(file)

    rows = []
    for record in raw_records:
        new_row = {}
        for key in record:
            value = record[key]
            if value is None:
                new_row[key] = None
            else:
                new_row[key] = str(value)
        rows.append(new_row)

    return rows


def load_since(rows, last_id):
    """Give this a list of rows you already loaded, and it
    hands back only the ones with an id bigger than last_id."""

    new_rows = []
    for row in rows:
        if int(row["id"]) > last_id:
            new_rows.append(row)
    return new_rows