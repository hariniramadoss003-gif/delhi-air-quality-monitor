from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import os
import sqlite3
import threading
import time
import requests
import pandas as pd
import joblib
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# =========================================================
# PATHS
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# If app.py is inside backend folder, project files are one level above
if os.path.basename(BASE_DIR).lower() == "backend":
    PROJECT_DIR = os.path.dirname(BASE_DIR)
else:
    PROJECT_DIR = BASE_DIR

DATABASE = os.path.join(BASE_DIR, "air_quality.db")

MODEL_PATH = os.path.join(PROJECT_DIR, "aqi_model.joblib")
FEATURES_PATH = os.path.join(PROJECT_DIR, "aqi_features.joblib")

# =========================================================
# LOCATION
# =========================================================

LATITUDE = 28.6139
LONGITUDE = 77.2090
LOCATION_NAME = "Delhi NCR"

# =========================================================
# LOAD ML MODEL
# =========================================================

model = None
feature_names = []

try:
    if os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)
        print("==========================================")
        print("ML MODEL LOADED SUCCESSFULLY")
        print("Model:", MODEL_PATH)
        print("==========================================")
    else:
        print("WARNING: ML model not found:", MODEL_PATH)

    if os.path.exists(FEATURES_PATH):
        feature_names = joblib.load(FEATURES_PATH)
        print("ML FEATURES LOADED:", feature_names)
    else:
        print("WARNING: Feature file not found:", FEATURES_PATH)

except Exception as e:
    print("ML LOAD ERROR:", e)


# =========================================================
# DATABASE
# =========================================================

def get_connection():
    conn = sqlite3.connect(DATABASE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():

    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS air_quality (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            aqi REAL,
            pm25 REAL,
            pm10 REAL,
            carbon_monoxide REAL,
            nitrogen_dioxide REAL,
            ozone REAL,
            temperature REAL,
            humidity REAL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            aqi REAL,
            level TEXT,
            message TEXT
        )
    """)

    conn.commit()
    conn.close()


init_database()


# =========================================================
# AQI LEVEL
# =========================================================

def get_aqi_level(aqi):

    try:
        aqi = float(aqi)
    except:
        return "Unknown"

    if aqi <= 50:
        return "Good"

    elif aqi <= 100:
        return "Moderate"

    elif aqi <= 200:
        return "Poor"

    elif aqi <= 300:
        return "Very Poor"

    else:
        return "Severe"


# =========================================================
# FETCH AIR QUALITY + WEATHER
# =========================================================

def fetch_current_data():

    try:

        air_url = (
            "https://air-quality-api.open-meteo.com/v1/air-quality"
            f"?latitude={LATITUDE}"
            f"&longitude={LONGITUDE}"
            "&current=pm2_5,pm10,carbon_monoxide,"
            "nitrogen_dioxide,ozone"
        )

        weather_url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={LATITUDE}"
            f"&longitude={LONGITUDE}"
            "&current=temperature_2m,relative_humidity_2m"
        )

        air_response = requests.get(air_url, timeout=20)
        weather_response = requests.get(weather_url, timeout=20)

        air_data = air_response.json()
        weather_data = weather_response.json()

        current_air = air_data.get("current", {})
        current_weather = weather_data.get("current", {})

        pm25 = current_air.get("pm2_5", 0)
        pm10 = current_air.get("pm10", 0)
        co = current_air.get("carbon_monoxide", 0)
        no2 = current_air.get("nitrogen_dioxide", 0)
        ozone = current_air.get("ozone", 0)

        temperature = current_weather.get("temperature_2m", 0)
        humidity = current_weather.get("relative_humidity_2m", 0)

        # Simple AQI estimation for display
        aqi = calculate_aqi(pm25, pm10, no2, ozone)

        result = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "location": LOCATION_NAME,
            "aqi": round(aqi, 2),
            "level": get_aqi_level(aqi),
            "pm25": pm25,
            "pm10": pm10,
            "carbon_monoxide": co,
            "nitrogen_dioxide": no2,
            "ozone": ozone,
            "temperature": temperature,
            "humidity": humidity
        }

        return result

    except Exception as e:

        print("DATA FETCH ERROR:", e)

        return None


# =========================================================
# SIMPLE AQI CALCULATION
# =========================================================

def calculate_aqi(pm25, pm10, no2, ozone):

    values = []

    try:
        if pm25 is not None:
            values.append(float(pm25) * 4)

        if pm10 is not None:
            values.append(float(pm10) * 2)

        if no2 is not None:
            values.append(float(no2))

        if ozone is not None:
            values.append(float(ozone))

    except:
        pass

    if not values:
        return 0

    return max(values)


# =========================================================
# SAVE DATA
# =========================================================

def save_air_quality(data):

    if not data:
        return

    conn = get_connection()

    conn.execute("""
        INSERT INTO air_quality
        (
            timestamp,
            aqi,
            pm25,
            pm10,
            carbon_monoxide,
            nitrogen_dioxide,
            ozone,
            temperature,
            humidity
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["timestamp"],
        data["aqi"],
        data["pm25"],
        data["pm10"],
        data["carbon_monoxide"],
        data["nitrogen_dioxide"],
        data["ozone"],
        data["temperature"],
        data["humidity"]
    ))

    conn.commit()
    conn.close()


# =========================================================
# SAVE ALERT
# =========================================================

def save_alert(data):

    if not data:
        return

    aqi = data["aqi"]
    level = data["level"]

    if aqi >= 200:

        message = "Air quality is very poor. Avoid unnecessary outdoor activity."

        conn = get_connection()

        conn.execute("""
            INSERT INTO alerts
            (timestamp, aqi, level, message)
            VALUES (?, ?, ?, ?)
        """, (
            data["timestamp"],
            aqi,
            level,
            message
        ))

        conn.commit()
        conn.close()


# =========================================================
# AUTOMATIC DATA COLLECTION
# =========================================================

def automatic_collection():

    while True:

        try:

            data = fetch_current_data()

            if data:

                save_air_quality(data)
                save_alert(data)

                print(
                    "Automatic data saved:",
                    data["timestamp"],
                    "AQI:",
                    data["aqi"]
                )

        except Exception as e:

            print("AUTO COLLECTION ERROR:", e)

        # Every 60 seconds
        time.sleep(60)


# Start automatic collection
collection_thread = threading.Thread(
    target=automatic_collection,
    daemon=True
)

collection_thread.start()


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def home():

    return send_from_directory(PROJECT_DIR, "index.html")


# =========================================================
# ENVIRONMENT / LIVE DATA
# =========================================================

@app.route("/environment")
def environment():

    data = fetch_current_data()

    if not data:

        return jsonify({
            "error": "Unable to fetch current air quality data"
        }), 500

    return jsonify(data)


# =========================================================
# HISTORY
# =========================================================

@app.route("/history")
def history():

    try:

        days = int(request.args.get("days", 1))

    except:

        days = 1

    if days not in [1, 7, 30]:

        days = 1

    start_time = datetime.now() - timedelta(days=days)

    conn = get_connection()

    rows = conn.execute("""
        SELECT *
        FROM air_quality
        WHERE timestamp >= ?
        ORDER BY timestamp ASC
    """, (
        start_time.strftime("%Y-%m-%d %H:%M:%S"),
    )).fetchall()

    conn.close()

    return jsonify([dict(row) for row in rows])


# =========================================================
# ALERT HISTORY
# =========================================================

@app.route("/alert-history")
def alert_history():

    conn = get_connection()

    rows = conn.execute("""
        SELECT *
        FROM alerts
        ORDER BY timestamp DESC
        LIMIT 100
    """).fetchall()

    conn.close()

    return jsonify([dict(row) for row in rows])


# =========================================================
# DATABASE STATUS
# =========================================================

@app.route("/database-status")
def database_status():

    conn = get_connection()

    count = conn.execute("""
        SELECT COUNT(*) AS count
        FROM air_quality
    """).fetchone()["count"]

    latest = conn.execute("""
        SELECT *
        FROM air_quality
        ORDER BY id DESC
        LIMIT 1
    """).fetchone()

    conn.close()

    return jsonify({
        "records": count,
        "latest": dict(latest) if latest else None
    })


# =========================================================
# ML FEATURE CREATION
# =========================================================

def create_ml_features(df):

    if df.empty:
        return df

    df = df.copy()

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    df["hour"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.dayofweek
    df["month"] = df["timestamp"].dt.month

    # Rolling PM2.5
    if "pm25" in df.columns:

        df["pm25_12hours"] = (
            df["pm25"]
            .rolling(window=12, min_periods=1)
            .mean()
        )

    else:

        df["pm25_12hours"] = 0

    # Ensure expected features exist
    for feature in feature_names:

        if feature not in df.columns:

            df[feature] = 0

    if feature_names:

        df = df[feature_names]

    return df


# =========================================================
# FORECAST
# =========================================================

@app.route("/forecast")
def forecast():

    if model is None:

        return jsonify({
            "error": "ML model not loaded"
        }), 500

    conn = get_connection()

    rows = conn.execute("""
        SELECT *
        FROM air_quality
        ORDER BY timestamp ASC
        LIMIT 200
    """).fetchall()

    conn.close()

    if not rows:

        return jsonify({
            "error": "No historical data available"
        }), 404

    df = pd.DataFrame([dict(row) for row in rows])

    try:

        features = create_ml_features(df)

        prediction = model.predict(features)

        latest_prediction = float(prediction[-1])

        forecasts = []

        for hours in [24, 48, 72]:

            forecasts.append({
                "hours": hours,
                "predicted_aqi": round(latest_prediction, 2),
                "level": get_aqi_level(latest_prediction)
            })

        return jsonify({
            "forecast": forecasts
        })

    except Exception as e:

        print("FORECAST ERROR:", e)

        return jsonify({
            "error": str(e)
        }), 500


# =========================================================
# STATIC FILES
# =========================================================

@app.route("/<path:filename>")
def static_files(filename):

    file_path = os.path.join(PROJECT_DIR, filename)

    if os.path.isfile(file_path):

        return send_from_directory(
            PROJECT_DIR,
            filename
        )

    return jsonify({
        "error": "File not found",
        "file": filename
    }), 404


# =========================================================
# RAILWAY / RENDER SERVER
# =========================================================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    print("==========================================")
    print("DELHI NCR AIR QUALITY MONITOR")
    print("Starting Flask server...")
    print("PORT:", port)
    print("==========================================")

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False
    )
