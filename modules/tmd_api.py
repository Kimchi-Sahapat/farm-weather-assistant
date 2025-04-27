# modules/tmd_api.py

import requests
import datetime

# 🧩 TMD API Credentials
UID = "u68sahapat"
UKEY = "8aa48a692a260d6f2319036fa75298cf"

# 🛰️ TMD API Endpoints
BASE_URL_HOURLY = "https://data.tmd.go.th/nwpapi/v1/forecast/location/hourly"
BASE_URL_DAILY = "https://data.tmd.go.th/nwpapi/v1/forecast/location/daily"
RADAR_IMAGE_URL = "https://hpc.tmd.go.th/radar/Composite_SRI.png"

# 🌦️ Fetch 72-hour Hourly Forecast
def fetch_hourly_forecast(lat: float, lon: float):
    params = {"uid": UID, "ukey": UKEY, "lat": lat, "lon": lon}
    try:
        response = requests.get(BASE_URL_HOURLY, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('WeatherForecasts', [])
    except Exception as e:
        print(f"⚠️ Error fetching hourly forecast: {e}")
        return []

# 📅 Fetch 10-day Daily Forecast
def fetch_daily_forecast(lat: float, lon: float):
    params = {"uid": UID, "ukey": UKEY, "lat": lat, "lon": lon}
    try:
        response = requests.get(BASE_URL_DAILY, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('WeatherForecasts', [])
    except Exception as e:
        print(f"⚠️ Error fetching daily forecast: {e}")
        return []

# 🌧️ Fetch Latest Radar Image URL
def fetch_radar_image() -> str:
    return RADAR_IMAGE_URL
