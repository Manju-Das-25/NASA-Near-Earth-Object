# NASA-Near-Earth-Object

This project provides an interactive Streamlit web application to explore NASA's Near-Earth Object (NEO) data using SQL queries on a local SQLite database.

## 📦 Features

- Interactive filters to explore asteroid data by:
  - Date
  - Distance (AU, Lunar)
  - Velocity
  - Diameter
  - Hazardous status
- 20+ predefined SQL queries to uncover insights like:
  - Fastest asteroids
  - Closest approaches
  - Brightest objects
  - Frequency of hazardous objects
- Visual exploration of NEOs using Streamlit

## 🛠️ Project Structure

- `proj.py` – Fetches, cleans, and stores NEO data into a local SQLite database.
- `app.py` – Streamlit app to query and explore the NEO data interactively.
- `nasa_neo.db` – SQLite database generated after running `proj.py`.
- `nasa_neo_data.json` – Raw JSON data from NASA API.

## 🚀 Getting Started

### Clone the Repository

```bash
git clone https://github.com/Manju-Das-25/NASA-Near-Earth-Object.git
cd nasa-neo-sql-explorer

Fetch and Load Data
Run this script to fetch data from the NASA API and populate the database:
python proj.py

Launch the Streamlit App
streamlit run app.py
