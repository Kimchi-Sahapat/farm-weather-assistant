# /modules/tmd_api.py

import requests

# TMD API credentials
UID = "u68sahapat"
UKEY = "8aa48a692a260d6f2319036fa75298cf"

# Fetch daily forecast (10 days)
def fetch_daily_forecast(lat, lon):
    try:
        response = requests.get(
            "https://data.tmd.go.th/nwpapi/v1/forecast/location/daily",
            params={"uid": UID, "ukey": UKEY, "lat": lat, "lon": lon},
            timeout=10
        )
        response.raise_for_status()
        return response.json().get('WeatherForecasts', [])
    except Exception as e:
        print(f"⚠️ Error fetching daily forecast: {e}")
        return []

# Fetch hourly forecast (72 hours)
def fetch_hourly_forecast(lat, lon):
    try:
        response = requests.get(
            "https://data.tmd.go.th/nwpapi/v1/forecast/location/hourly",
            params={"uid": UID, "ukey": UKEY, "lat": lat, "lon": lon},
            timeout=10
        )
        response.raise_for_status()
        return response.json().get('WeatherForecasts', [])
    except Exception as e:
        print(f"⚠️ Error fetching hourly forecast: {e}")
        return []

# Static radar image
def fetch_radar_image():
    return "https://hpc.tmd.go.th/radar/Composite_SRI.png"
