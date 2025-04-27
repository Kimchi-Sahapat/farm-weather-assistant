import requests
import datetime

# Your TMD API credentials
UID = "u68sahapat"
UKEY = "8aa48a692a260d6f2319036fa75298cf"

# API Base URLs
BASE_URL_HOURLY = "https://data.tmd.go.th/nwpapi/v1/forecast/location/hourly"
BASE_URL_DAILY = "https://data.tmd.go.th/nwpapi/v1/forecast/location/daily"
RADAR_URL = "https://hpc.tmd.go.th/radar/Composite_SRI.png"

# Function to fetch 72-hour hourly forecast
def fetch_hourly_forecast(lat, lon):
    try:
        params = {
            "uid": UID,
            "ukey": UKEY,
            "lat": lat,
            "lon": lon
        }
        response = requests.get(BASE_URL_HOURLY, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('WeatherForecasts', [])
    except Exception as e:
        print(f"⚠️ Could not fetch hourly forecast: {e}")
        return []

# Function to fetch 10-day daily forecast
def fetch_daily_forecast(lat, lon):
    try:
        params = {
            "uid": UID,
            "ukey": UKEY,
            "lat": lat,
            "lon": lon
        }
        response = requests.get(BASE_URL_DAILY, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('WeatherForecasts', [])
    except Exception as e:
        print(f"⚠️ Could not fetch daily forecast: {e}")
        return []

# Function to get radar image URL
def fetch_radar_image():
    # Static radar image link provided
    return RADAR_URL
