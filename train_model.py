import requests
import pandas as pd
import numpy as np
import joblib

from sklearn.ensemble import RandomForestRegressor
from datetime import datetime, timedelta


# ==========================================
# DELHI NCR LOCATION
# ==========================================

LATITUDE = 28.6139
LONGITUDE = 77.2090


# ==========================================
# DATE RANGE
# ==========================================

END_DATE = (
    datetime.utcnow().date() - timedelta(days=5)
)

START_DATE = (
    END_DATE - timedelta(days=365)
)


# ==========================================
# HISTORICAL AIR QUALITY DATA
# ==========================================

url = (
    "https://air-quality-api.open-meteo.com/v1/air-quality"
    f"?latitude={LATITUDE}"
    f"&longitude={LONGITUDE}"
    f"&start_date={START_DATE}"
    f"&end_date={END_DATE}"
    "&hourly="
    "pm2_5,"
    "pm10,"
    "nitrogen_dioxide,"
    "sulphur_dioxide,"
    "carbon_monoxide,"
    "ozone"
    "&timezone=Asia%2FKolkata"
)


print()
print("==========================================")
print("DOWNLOADING HISTORICAL DATA")
print("==========================================")


try:

    response = requests.get(
        url,
        timeout=60
    )

    response.raise_for_status()

except requests.RequestException as error:

    print("API request failed.")
    print(error)
    raise SystemExit


data = response.json()


# ==========================================
# DATAFRAME
# ==========================================

hourly = data.get(
    "hourly",
    {}
)


df = pd.DataFrame(
    hourly
)


print(
    "Total records downloaded:",
    len(df)
)


# ==========================================
# CLEAN DATA
# ==========================================

df["time"] = pd.to_datetime(
    df["time"]
)


df = df.dropna()


# ==========================================
# AQI CALCULATION
# ==========================================

def calculate_aqi(pm25):

    if pm25 <= 30:

        return (
            pm25 / 30
        ) * 50


    elif pm25 <= 60:

        return (
            51 +
            ((pm25 - 30) / 30) * 49
        )


    elif pm25 <= 90:

        return (
            101 +
            ((pm25 - 60) / 30) * 99
        )


    elif pm25 <= 120:

        return (
            201 +
            ((pm25 - 90) / 30) * 99
        )


    elif pm25 <= 250:

        return (
            301 +
            ((pm25 - 120) / 130) * 99
        )


    else:

        return (
            401 +
            ((pm25 - 250) / 250) * 99
        )


df["AQI"] = df[
    "pm2_5"
].apply(
    calculate_aqi
)


# ==========================================
# CREATE FUTURE AQI TARGET
# ==========================================

# AQI 24 hours into the future

df["future_AQI"] = (
    df["AQI"].shift(-24)
)


# Remove rows where future AQI is unavailable

df = df.dropna()


# ==========================================
# TIME FEATURES
# ==========================================

df["hour"] = (
    df["time"].dt.hour
)


df["day"] = (
    df["time"].dt.day
)


df["month"] = (
    df["time"].dt.month
)


df["day_of_week"] = (
    df["time"].dt.dayofweek
)


# ==========================================
# ADD POLLUTION LAG FEATURES
# ==========================================

df["pm25_previous"] = (
    df["pm2_5"].shift(1)
)


df["pm25_3hours"] = (
    df["pm2_5"].shift(3)
)


df["pm25_6hours"] = (
    df["pm2_5"].shift(6)
)


df["pm25_12hours"] = (
    df["pm2_5"].shift(12)
)


df["pm25_24hours"] = (
    df["pm2_5"].shift(24)
)


df = df.dropna()


# ==========================================
# MACHINE LEARNING FEATURES
# ==========================================

features = [

    "pm2_5",

    "pm10",

    "nitrogen_dioxide",

    "sulphur_dioxide",

    "carbon_monoxide",

    "ozone",

    "pm25_previous",

    "pm25_3hours",

    "pm25_6hours",

    "pm25_12hours",

    "pm25_24hours",

    "hour",

    "day",

    "month",

    "day_of_week"

]


X = df[
    features
]


# ==========================================
# TARGET
# ==========================================

y = df[
    "future_AQI"
]


print()
print("==========================================")
print("PREPARING ML DATA")
print("==========================================")

print(
    "Training records:",
    len(df)
)


# ==========================================
# RANDOM FOREST MODEL
# ==========================================

print()
print(
    "Training Random Forest forecasting model..."
)


model = RandomForestRegressor(

    n_estimators=150,

    max_depth=18,

    min_samples_leaf=2,

    random_state=42,

    n_jobs=-1
)


model.fit(
    X,
    y
)


# ==========================================
# SAVE MODEL
# ==========================================

joblib.dump(
    model,
    "aqi_model.joblib"
)


# ==========================================
# SAVE FEATURE INFORMATION
# ==========================================

joblib.dump(
    features,
    "aqi_features.joblib"
)


# ==========================================
# COMPLETED
# ==========================================

print()
print("==========================================")
print("ML FORECASTING MODEL TRAINED")
print("==========================================")

print(
    "Training records:",
    len(df)
)

print(
    "Target:",
    "AQI 24 hours into the future"
)

print(
    "Model:",
    "Random Forest Regressor"
)

print(
    "Model saved as:",
    "aqi_model.joblib"
)

print(
    "Features saved as:",
    "aqi_features.joblib"
)

print("==========================================")