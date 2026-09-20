from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import sqlite3
import requests
import pandas as pd
import joblib
import os
import threading
import time
from datetime import datetime

# =========================================================
# PATHS
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

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
# FLASK
# =========================================================

app = Flask(__name__)
CORS(app, origins="*")

# =========================================================
# ML MODEL
# =========================================================

try:
    model = joblib.load(MODEL_PATH)
    features = joblib.load(FEATURES_PATH)

    print("==========================================")
    print("ML MODEL LOADED SUCCESSFULLY")
    print("Model:", MODEL_PATH)
    print("Features:", features)
    print("==========================================")

except Exception as e:

    model = None
    features = []

    print("ML MODEL ERROR:", e)


# =========================================================
# DATABASE
# =========================================================

def init_database():

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS air_quality_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            pm25 REAL,
            pm10 REAL,
            no2 REAL,
            so2 REAL,
            co REAL,
            o3 REAL,
            aqi REAL,
            temperature REAL,
            humidity REAL,
            wind_speed REAL,
            wind_direction REAL,
            rainfall REAL
        )
    """)

    conn.commit()
    conn.close()

    print("DATABASE READY")


init_database()


# =========================================================
# AQI CALCULATION
# =========================================================

def calculate_aqi(pm25):

    if pm25 is None:
        return 0

    try:
        pm25 = float(pm25)
    except:
        return 0

    if pm25 <= 12:
        aqi = pm25 * 50 / 12

    elif pm25 <= 35.4:
        aqi = 50 + (pm25 - 12) * 50 / (35.4 - 12)

    elif pm25 <= 55.4:
        aqi = 100 + (pm25 - 35.4) * 50 / (55.4 - 35.4)

    elif pm25 <= 150.4:
        aqi = 150 + (pm25 - 55.4) * 50 / (150.4 - 55.4)

    elif pm25 <= 250.4:
        aqi = 200 + (pm25 - 150.4) * 50 / (250.4 - 150.4)

    else:
        aqi = 300 + (pm25 - 250.4) * 100 / 249.6

    return round(aqi, 2)


# =========================================================
# AQI CATEGORY
# =========================================================

def get_aqi_category(aqi):

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
# SAVE READING
# =========================================================

def save_reading(data):

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO air_quality_readings
        (
            timestamp,
            pm25,
            pm10,
            no2,
            so2,
            co,
            o3,
            aqi,
            temperature,
            humidity,
            wind_speed,
            wind_direction,
            rainfall
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["timestamp"],
        data["pm25"],
        data["pm10"],
        data["no2"],
        data["so2"],
        data["co"],
        data["o3"],
        data["aqi"],
        data["temperature"],
        data["humidity"],
        data["wind_speed"],
        data["wind_direction"],
        data["rainfall"]
    ))

    conn.commit()
    conn.close()


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return send_from_directory(
        PROJECT_DIR,
        "index.html"
    )


# =========================================================
# ENVIRONMENT
# =========================================================

@app.route("/environment")
def environment():

    try:

        air_url = "https://air-quality-api.open-meteo.com/v1/air-quality"

        air_params = {
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "current": "pm2_5,pm10,nitrogen_dioxide,sulphur_dioxide,carbon_monoxide,ozone"
        }

        air_response = requests.get(
            air_url,
            params=air_params,
            timeout=20
        )

        air_data = air_response.json()
        current_air = air_data.get("current", {})

        weather_url = "https://api.open-meteo.com/v1/forecast"

        weather_params = {
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,precipitation"
        }

        weather_response = requests.get(
            weather_url,
            params=weather_params,
            timeout=20
        )

        weather_data = weather_response.json()
        current_weather = weather_data.get("current", {})

        pm25 = current_air.get("pm2_5", 0)
        pm10 = current_air.get("pm10", 0)
        no2 = current_air.get("nitrogen_dioxide", 0)
        so2 = current_air.get("sulphur_dioxide", 0)
        co = current_air.get("carbon_monoxide", 0)
        o3 = current_air.get("ozone", 0)

        temperature = current_weather.get("temperature_2m", 0)
        humidity = current_weather.get("relative_humidity_2m", 0)
        wind_speed = current_weather.get("wind_speed_10m", 0)
        wind_direction = current_weather.get("wind_direction_10m", 0)
        rainfall = current_weather.get("precipitation", 0)

        aqi = calculate_aqi(pm25)
        category = get_aqi_category(aqi)

        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        reading = {
            "timestamp": timestamp,
            "pm25": pm25,
            "pm10": pm10,
            "no2": no2,
            "so2": so2,
            "co": co,
            "o3": o3,
            "aqi": aqi,
            "temperature": temperature,
            "humidity": humidity,
            "wind_speed": wind_speed,
            "wind_direction": wind_direction,
            "rainfall": rainfall
        }

        save_reading(reading)

        if aqi <= 50:
            explanation = "Air quality is good. Outdoor activities are generally suitable."

        elif aqi <= 100:
            explanation = "Air quality is moderate. Sensitive people should monitor conditions."

        elif aqi <= 200:
            explanation = "Air quality is poor. Reduce prolonged outdoor exposure."

        elif aqi <= 300:
            explanation = "Air quality is very poor. Avoid unnecessary outdoor exposure."

        else:
            explanation = "Air quality is severe. Take precautions and reduce outdoor exposure."

        return jsonify({

            "status": "success",
            "location": LOCATION_NAME,
            "timestamp": timestamp,

            "aqi": aqi,
            "category": category,

            "pm25": pm25,
            "pm10": pm10,
            "no2": no2,
            "so2": so2,
            "co": co,
            "o3": o3,

            "temperature": temperature,
            "humidity": humidity,
            "wind_speed": wind_speed,
            "wind_direction": wind_direction,
            "rainfall": rainfall,

            "ai_explanation": explanation

        })

    except Exception as e:

        print("Environment error:", e)

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# =========================================================
# HISTORY
# =========================================================

@app.route("/history")
def history():

    try:

        days = request.args.get(
            "days",
            default=1,
            type=int
        )

        if days not in [1, 7, 30]:
            days = 1

        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM air_quality_readings
            WHERE datetime(timestamp) >= datetime('now', ?)
            ORDER BY timestamp DESC
            LIMIT 1000
        """, (f"-{days} days",))

        rows = cursor.fetchall()

        conn.close()

        data = [dict(row) for row in rows]

        return jsonify({

            "status": "success",
            "days": days,
            "count": len(data),
            "data": data

        })

    except Exception as e:

        print("History error:", e)

        return jsonify({

            "status": "error",
            "message": str(e),
            "data": []

        }), 500


# =========================================================
# ALERT HISTORY
# =========================================================

@app.route("/alert-history")
def alert_history():

    try:

        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                timestamp,
                aqi,
                pm25,
                pm10
            FROM air_quality_readings
            WHERE aqi > 100
            ORDER BY timestamp DESC
            LIMIT 100
        """)

        rows = cursor.fetchall()

        conn.close()

        alerts = []

        for row in rows:

            aqi = row["aqi"]

            if aqi <= 200:
                level = "Poor"

            elif aqi <= 300:
                level = "Very Poor"

            else:
                level = "Severe"

            alerts.append({

                "id": row["id"],
                "timestamp": row["timestamp"],
                "aqi": row["aqi"],
                "level": level,
                "pm25": row["pm25"],
                "pm10": row["pm10"]

            })

        return jsonify({

            "status": "success",
            "count": len(alerts),
            "data": alerts

        })

    except Exception as e:

        print("Alert history error:", e)

        return jsonify({

            "status": "error",
            "message": str(e),
            "data": []

        }), 500


# =========================================================
# DATABASE STATUS
# =========================================================

@app.route("/database-status")
def database_status():

    try:

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*)
            FROM air_quality_readings
        """)

        count = cursor.fetchone()[0]

        conn.close()

        return jsonify({

            "status": "success",
            "count": count

        })

    except Exception as e:

        return jsonify({

            "status": "error",
            "message": str(e)

        }), 500


# =========================================================
# ML FEATURES
# =========================================================

def create_ml_features(df):

    result = pd.DataFrame(index=df.index)

    for feature in features:

        if feature in df.columns:

            result[feature] = df[feature]

        elif feature == "day_of_week":

            result[feature] = pd.to_datetime(
                df["timestamp"]
            ).dt.dayofweek

        elif feature == "hour":

            result[feature] = pd.to_datetime(
                df["timestamp"]
            ).dt.hour

        elif feature == "month":

            result[feature] = pd.to_datetime(
                df["timestamp"]
            ).dt.month

        elif feature == "pm25_12hours":

            result[feature] = (
                df["pm25"]
                .rolling(12)
                .mean()
                .bfill()
            )

        elif feature == "pm25_24hours":

            result[feature] = (
                df["pm25"]
                .rolling(24)
                .mean()
                .bfill()
            )

        elif feature == "aqi_12hours":

            result[feature] = (
                df["aqi"]
                .rolling(12)
                .mean()
                .bfill()
            )

        elif feature == "aqi_24hours":

            result[feature] = (
                df["aqi"]
                .rolling(24)
                .mean()
                .bfill()
            )

        else:

            result[feature] = 0

    return result


# =========================================================
# FORECAST
# =========================================================

@app.route("/forecast")
def forecast():

    try:

        if model is None:

            return jsonify({
                "status": "error",
                "message": "ML model is not loaded."
            }), 500

        forecast_url = (
            "https://air-quality-api.open-meteo.com/v1/air-quality"
        )

        params = {

            "latitude": LATITUDE,
            "longitude": LONGITUDE,

            "hourly":
                "pm2_5,pm10,nitrogen_dioxide,"
                "sulphur_dioxide,carbon_monoxide,ozone",

            "forecast_days": 3,
            "timezone": "auto"

        }

        response = requests.get(
            forecast_url,
            params=params,
            timeout=20
        )

        api_data = response.json()

        hourly = api_data.get(
            "hourly",
            {}
        )

        times = hourly.get(
            "time",
            []
        )

        df = pd.DataFrame({

            "timestamp": times,

            "pm25": hourly.get(
                "pm2_5",
                []
            ),

            "pm10": hourly.get(
                "pm10",
                []
            ),

            "no2": hourly.get(
                "nitrogen_dioxide",
                []
            ),

            "so2": hourly.get(
                "sulphur_dioxide",
                []
            ),

            "co": hourly.get(
                "carbon_monoxide",
                []
            ),

            "o3": hourly.get(
                "ozone",
                []
            )

        })

        if df.empty:

            return jsonify({

                "status": "error",
                "message": "No forecast data available."

            }), 500

        df["aqi"] = df["pm25"].apply(
            calculate_aqi
        )

        ml_features = create_ml_features(df)

        predictions = model.predict(
            ml_features
        )

        predictions = [
            round(float(x), 2)
            for x in predictions
        ]

        predictions = predictions[:72]

        result = []

        for i, value in enumerate(predictions):

            result.append({

                "timestamp": df.iloc[i]["timestamp"],
                "aqi": value,
                "category": get_aqi_category(value)

            })

        return jsonify({

            "status": "success",
            "location": LOCATION_NAME,
            "forecast_hours": len(result),
            "data": result

        })

    except Exception as e:

        print("Forecast error:", e)

        return jsonify({

            "status": "error",
            "message": str(e)

        }), 500


# =========================================================
# AUTOMATIC DATA COLLECTION
# =========================================================

def automatic_data_collection():

    print("==========================================")
    print("AUTOMATIC DATA COLLECTION STARTED")
    print("Testing interval: 1 minute")
    print("==========================================")

    try:

        with app.test_request_context():
            environment()

    except Exception as e:

        print(
            "Initial collection error:",
            e
        )

    while True:

        try:

            time.sleep(60)

            with app.test_request_context():
                environment()

            print(
                "Automatic historical reading collected:",
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )

        except Exception as e:

            print(
                "Automatic collection error:",
                e
            )


# =========================================================
# START AUTOMATIC COLLECTION
# =========================================================

collector_thread = threading.Thread(
    target=automatic_data_collection,
    daemon=True
)

collector_thread.start()


# =========================================================
# STATIC FILE ROUTE
# IMPORTANT: KEEP THIS AT THE VERY END
# =========================================================

@app.route("/<path:filename>")
def static_files(filename):

    return send_from_directory(
        PROJECT_DIR,
        filename
    )


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    print("==========================================")
    print("DELHI NCR AIR QUALITY MONITOR")
    print("SERVER STARTING...")
    print("http://127.0.0.1:5000")
    print("==========================================")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
        use_reloader=False
    )