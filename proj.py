# proj.py

import requests
import json
import sqlite3
from datetime import datetime
import pandas as pd

# Configuration
API_KEY = "6TrUCudO8f2xRLAReucUzAPK6lHbf1CGKwI9fkxm"
START_DATE = "2024-01-01"
DATA_FILENAME = 'nasa_neo_data.json'
DB_FILE = 'nasa_neo.db'

# -------------------- Core Functions --------------------

def fetch_neo_data_from_api():
    all_asteroid_records = []
    current_url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={START_DATE}&api_key={API_KEY}"

    while len(all_asteroid_records) < 10000:
        response = requests.get(current_url)
        data = response.json()
        for date in data['near_earth_objects']:
            for asteroid in data['near_earth_objects'][date]:
                if 'close_approach_data' in asteroid and asteroid['close_approach_data']:
                    for approach in asteroid['close_approach_data']:
                        record = {
                            'id': asteroid.get('id'),
                            'neo_reference_id': asteroid.get('neo_reference_id'),
                            'name': asteroid.get('name'),
                            'absolute_magnitude_h': asteroid.get('absolute_magnitude_h'),
                            'estimated_diameter_min_km': asteroid.get('estimated_diameter', {}).get('kilometers', {}).get('estimated_diameter_min'),
                            'estimated_diameter_max_km': asteroid.get('estimated_diameter', {}).get('kilometers', {}).get('estimated_diameter_max'),
                            'is_potentially_hazardous_asteroid': asteroid.get('is_potentially_hazardous_asteroid'),
                            'close_approach_date': approach.get('close_approach_date'),
                            'relative_velocity_kmph': approach.get('relative_velocity', {}).get('kilometers_per_hour'),
                            'miss_distance_km': approach.get('miss_distance', {}).get('kilometers'),
                            'miss_distance_lunar': approach.get('miss_distance', {}).get('lunar'),
                            'miss_distance_astronomical': approach.get('miss_distance', {}).get('astronomical'),
                            'orbiting_body': approach.get('orbiting_body')
                        }
                        all_asteroid_records.append(record)
        current_url = data['links']['next']
    return all_asteroid_records[:10000]

def clean_and_prepare_data(records):
    cleaned_records = []
    for record in records:
        try:
            record['absolute_magnitude_h'] = float(record['absolute_magnitude_h']) if record.get('absolute_magnitude_h') else None
            record['estimated_diameter_min_km'] = float(record['estimated_diameter_min_km']) if record.get('estimated_diameter_min_km') else None
            record['estimated_diameter_max_km'] = float(record['estimated_diameter_max_km']) if record.get('estimated_diameter_max_km') else None
            record['relative_velocity_kmph'] = float(record['relative_velocity_kmph']) if record.get('relative_velocity_kmph') else None
            record['miss_distance_km'] = float(record['miss_distance_km']) if record.get('miss_distance_km') else None
            record['miss_distance_lunar'] = float(record['miss_distance_lunar']) if record.get('miss_distance_lunar') else None
            record['miss_distance_astronomical'] = float(record['miss_distance_astronomical']) if record.get('miss_distance_astronomical') else None

            if record.get('close_approach_date'):
                datetime.strptime(record['close_approach_date'], '%Y-%m-%d')
                cleaned_records.append(record)
        except:
            continue
    return cleaned_records

def setup_database_and_insert_data(records):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS asteroids (
            id TEXT PRIMARY KEY,
            name TEXT,
            absolute_magnitude_h REAL,
            estimated_diameter_min_km REAL,
            estimated_diameter_max_km REAL,
            is_potentially_hazardous_asteroid INTEGER
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS close_approach (
            neo_reference_id TEXT,
            close_approach_date DATE,
            relative_velocity_kmph REAL,
            miss_distance_astronomical REAL,
            miss_distance_km REAL,
            miss_distance_lunar REAL,
            orbiting_body TEXT,
            FOREIGN KEY (neo_reference_id) REFERENCES asteroids (id)
        )
    ''')

    for record in records:
        cursor.execute('''
            INSERT OR IGNORE INTO asteroids VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            record['id'], record['name'], record['absolute_magnitude_h'],
            record['estimated_diameter_min_km'], record['estimated_diameter_max_km'],
            1 if record['is_potentially_hazardous_asteroid'] else 0
        ))

        cursor.execute('''
            INSERT INTO close_approach VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            record['neo_reference_id'], record['close_approach_date'],
            record['relative_velocity_kmph'], record['miss_distance_astronomical'],
            record['miss_distance_km'], record['miss_distance_lunar'],
            record['orbiting_body']
        ))

    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def run_query(query, params=()):
    conn = get_db_connection()
    return pd.read_sql_query(query, conn, params=params)

# -------------------- EXECUTE FULL PIPELINE WHEN RUN --------------------

if __name__ == "__main__":
    print("Fetching data from NASA API...")
    raw_data = fetch_neo_data_from_api()

    print(f"Saving {len(raw_data)} records to JSON...")
    with open(DATA_FILENAME, 'w') as f:
        json.dump(raw_data, f, indent=4)

    print("Cleaning data...")
    cleaned_data = clean_and_prepare_data(raw_data)

    print("Inserting into SQLite database...")
    setup_database_and_insert_data(cleaned_data)

    print("✅ All done! Data saved to 'nasa_neo.db' and 'nasa_neo_data.json'.")
