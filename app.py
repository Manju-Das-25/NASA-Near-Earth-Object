# app.py
import streamlit as st
from datetime import datetime
from proj import run_query, get_db_connection
import sqlite3

st.set_page_config(page_title="NASA NEO SQL Explorer", layout="wide")
st.title("🚀 NASA Near-Earth Object (NEO) SQL Insights")

# --- Sidebar: Filters and Predefined Queries ---
st.sidebar.header("🔍 Query Options")

selected_query = st.sidebar.selectbox(
    "Choose a predefined SQL query:",
    [
        "1. Count how many times each asteroid has approached Earth",
        "2. Average velocity of each asteroid over multiple approaches",
        "3. List top 10 fastest asteroids",
        "4. Potentially hazardous asteroids with >3 approaches",
        "5. Month with most asteroid approaches",
        "6. Asteroid with fastest ever approach",
        "7. Asteroids sorted by max estimated diameter",
        "8. Asteroids with decreasing miss distance over time",
        "9. Closest approach for each asteroid",
        "10. Asteroids with velocity > 50,000 km/h",
        "11. Number of approaches per month",
        "12. Asteroid with highest brightness (lowest magnitude)",
        "13. Hazardous vs Non-Hazardous asteroid counts",
        "14. Asteroids that passed closer than the Moon",
        "15. Asteroids within 0.05 AU",
        "16. Top 5 largest hazardous asteroids",
        "17. Average miss distance per year",
        "18. Most frequent orbiting body",
        "19. Earliest recorded asteroid approach",
        "20. Average diameter of non-hazardous asteroids"
    ]
)

# --- Sidebar: Filter Criteria ---
st.sidebar.markdown("---")
st.sidebar.header("📅 Filter Asteroids by Attributes")

conn = get_db_connection()

min_date, max_date = conn.execute("SELECT MIN(close_approach_date), MAX(close_approach_date) FROM close_approach").fetchone()
min_au, max_au = conn.execute("SELECT MIN(miss_distance_astronomical), MAX(miss_distance_astronomical) FROM close_approach").fetchone()
min_ld, max_ld = conn.execute("SELECT MIN(miss_distance_lunar), MAX(miss_distance_lunar) FROM close_approach").fetchone()
min_vel, max_vel = conn.execute("SELECT MIN(relative_velocity_kmph), MAX(relative_velocity_kmph) FROM close_approach").fetchone()
min_dmin, max_dmin = conn.execute("SELECT MIN(estimated_diameter_min_km), MAX(estimated_diameter_min_km) FROM asteroids").fetchone()
min_dmax, max_dmax = conn.execute("SELECT MIN(estimated_diameter_max_km), MAX(estimated_diameter_max_km) FROM asteroids").fetchone()

start_date = st.sidebar.date_input("Start Date", datetime.strptime(min_date, "%Y-%m-%d"))
end_date = st.sidebar.date_input("End Date", datetime.strptime(max_date, "%Y-%m-%d"))
au_range = st.sidebar.slider("Astronomical Units (AU)", float(min_au), float(max_au), (float(min_au), float(max_au)))
ld_range = st.sidebar.slider("Lunar Distance (LD)", float(min_ld), float(max_ld), (float(min_ld), float(max_ld)))
velocity_range = st.sidebar.slider("Relative Velocity (km/h)", float(min_vel), float(max_vel), (float(min_vel), float(max_vel)))
dmin_range = st.sidebar.slider("Estimated Diameter Min (km)", float(min_dmin), float(max_dmin), (float(min_dmin), float(max_dmin)))
dmax_range = st.sidebar.slider("Estimated Diameter Max (km)", float(min_dmax), float(max_dmax), (float(min_dmax), float(max_dmax)))
hazardous = st.sidebar.selectbox("Hazardous State", ["All", "Yes", "No"])

# --- Query Map ---
QUERIES = {
    "1. Count how many times each asteroid has approached Earth": """
        SELECT name, COUNT(*) AS approach_count
        FROM asteroids a
        JOIN close_approach ca ON a.id = ca.neo_reference_id
        GROUP BY name
        ORDER BY approach_count DESC;
    """,
    "2. Average velocity of each asteroid over multiple approaches": """
        SELECT name, ROUND(AVG(ca.relative_velocity_kmph), 2) AS avg_velocity_kmph
        FROM asteroids a
        JOIN close_approach ca ON a.id = ca.neo_reference_id
        GROUP BY name
        ORDER BY avg_velocity_kmph DESC;
    """,
    "3. List top 10 fastest asteroids": """
        SELECT name, MAX(ca.relative_velocity_kmph) AS max_velocity_kmph
        FROM asteroids a
        JOIN close_approach ca ON a.id = ca.neo_reference_id
        GROUP BY name
        ORDER BY max_velocity_kmph DESC
        LIMIT 10;
    """,
    "4. Potentially hazardous asteroids with >3 approaches": """
        SELECT name, COUNT(*) AS approach_count
        FROM asteroids a
        JOIN close_approach ca ON a.id = ca.neo_reference_id
        WHERE is_potentially_hazardous_asteroid = 1
        GROUP BY name
        HAVING COUNT(*) > 3
        ORDER BY approach_count DESC;
    """,
    "5. Month with most asteroid approaches": """
        SELECT strftime('%Y-%m', close_approach_date) AS month,
               COUNT(*) AS approach_count
        FROM close_approach
        GROUP BY month
        ORDER BY approach_count DESC
        LIMIT 1;
    """,
    "6. Asteroid with fastest ever approach": """
        SELECT name, ca.relative_velocity_kmph, ca.close_approach_date
        FROM asteroids a
        JOIN close_approach ca ON a.id = ca.neo_reference_id
        ORDER BY ca.relative_velocity_kmph DESC
        LIMIT 1;
    """,
    "7. Asteroids sorted by max estimated diameter": """
        SELECT name, estimated_diameter_max_km
        FROM asteroids
        ORDER BY estimated_diameter_max_km DESC;
    """,
    "8. Asteroids with decreasing miss distance over time": """
        SELECT a.name, ca.close_approach_date, ca.miss_distance_km
        FROM asteroids a
        JOIN close_approach ca ON a.id = ca.neo_reference_id
        ORDER BY a.name, ca.close_approach_date;
    """,
    "9. Closest approach for each asteroid": """
        SELECT name, ca.close_approach_date, MIN(ca.miss_distance_km) AS closest_km
        FROM asteroids a
        JOIN close_approach ca ON a.id = ca.neo_reference_id
        GROUP BY name
        ORDER BY closest_km ASC;
    """,
    "10. Asteroids with velocity > 50,000 km/h": """
        SELECT DISTINCT name
        FROM asteroids a
        JOIN close_approach ca ON a.id = ca.neo_reference_id
        WHERE ca.relative_velocity_kmph > 50000
        ORDER BY name;
    """,
    "11. Number of approaches per month": """
        SELECT strftime('%Y-%m', close_approach_date) AS month,
               COUNT(*) AS approach_count
        FROM close_approach
        GROUP BY month
        ORDER BY month;
    """,
    "12. Asteroid with highest brightness (lowest magnitude)": """
        SELECT name, absolute_magnitude_h
        FROM asteroids
        WHERE absolute_magnitude_h IS NOT NULL
        ORDER BY absolute_magnitude_h ASC
        LIMIT 1;
    """,
    "13. Hazardous vs Non-Hazardous asteroid counts": """
        SELECT CASE WHEN is_potentially_hazardous_asteroid = 1 THEN 'Hazardous' ELSE 'Non-Hazardous' END AS type,
               COUNT(*) AS count
        FROM asteroids
        GROUP BY type;
    """,
    "14. Asteroids that passed closer than the Moon": """
        SELECT name, ca.close_approach_date, ca.miss_distance_lunar
        FROM asteroids a
        JOIN close_approach ca ON a.id = ca.neo_reference_id
        WHERE ca.miss_distance_lunar < 1
        ORDER BY ca.miss_distance_lunar ASC;
    """,
    "15. Asteroids within 0.05 AU": """
        SELECT name, ca.close_approach_date, ca.miss_distance_astronomical
        FROM asteroids a
        JOIN close_approach ca ON a.id = ca.neo_reference_id
        WHERE ca.miss_distance_astronomical < 0.05
        ORDER BY ca.miss_distance_astronomical ASC;
    """,
    "16. Top 5 largest hazardous asteroids": """
        SELECT name, estimated_diameter_max_km
        FROM asteroids
        WHERE is_potentially_hazardous_asteroid = 1
        ORDER BY estimated_diameter_max_km DESC
        LIMIT 5;
    """,
    "17. Average miss distance per year": """
        SELECT strftime('%Y', close_approach_date) AS year,
               ROUND(AVG(miss_distance_km), 2) AS avg_miss_km
        FROM close_approach
        GROUP BY year
        ORDER BY year;
    """,
    "18. Most frequent orbiting body": """
        SELECT orbiting_body, COUNT(*) AS count
        FROM close_approach
        GROUP BY orbiting_body
        ORDER BY count DESC
        LIMIT 1;
    """,
    "19. Earliest recorded asteroid approach": """
        SELECT name, MIN(close_approach_date) AS first_approach
        FROM asteroids a
        JOIN close_approach ca ON a.id = ca.neo_reference_id;
    """,
    "20. Average diameter of non-hazardous asteroids": """
        SELECT ROUND(AVG(estimated_diameter_min_km), 3) AS avg_min,
               ROUND(AVG(estimated_diameter_max_km), 3) AS avg_max
        FROM asteroids
        WHERE is_potentially_hazardous_asteroid = 0;
    """
}

if st.sidebar.button("Run Predefined Query"):
    df = run_query(QUERIES[selected_query])
    st.subheader(f"Results for: {selected_query}")
    st.dataframe(df, use_container_width=True)

# --- Combined Filtered Query ---
st.markdown("---")
st.header("📊 Filtered Asteroid Data")

filtered_sql = f"""
    SELECT a.name, ca.close_approach_date, ca.relative_velocity_kmph,
           ca.miss_distance_astronomical, ca.miss_distance_lunar,
           a.estimated_diameter_min_km, a.estimated_diameter_max_km,
           a.is_potentially_hazardous_asteroid
    FROM asteroids a
    JOIN close_approach ca ON a.id = ca.neo_reference_id
    WHERE ca.close_approach_date BETWEEN '{start_date}' AND '{end_date}'
      AND ca.miss_distance_astronomical BETWEEN {au_range[0]} AND {au_range[1]}
      AND ca.miss_distance_lunar BETWEEN {ld_range[0]} AND {ld_range[1]}
      AND ca.relative_velocity_kmph BETWEEN {velocity_range[0]} AND {velocity_range[1]}
      AND a.estimated_diameter_min_km BETWEEN {dmin_range[0]} AND {dmin_range[1]}
      AND a.estimated_diameter_max_km BETWEEN {dmax_range[0]} AND {dmax_range[1]}
"""

if hazardous == "Yes":
    filtered_sql += " AND a.is_potentially_hazardous_asteroid = 1"
elif hazardous == "No":
    filtered_sql += " AND a.is_potentially_hazardous_asteroid = 0"

filtered_sql += " ORDER BY ca.close_approach_date DESC;"

if st.button("Apply Filters"):
    result = run_query(filtered_sql)
    st.dataframe(result, use_container_width=True)
