import requests
import streamlit as st
from datetime import datetime, timedelta

# TMD API Endpoints
TMD_HOURLY_API = "https://data.tmd.go.th/nwpapi/v1/forecast/location/hourly"
TMD_DAILY_API = "https://data.tmd.go.th/nwpapi/v1/forecast/location/daily"
TMD_NOWCAST_API = "https://data.tmd.go.th/nwpapi/v1/forecast/area/nowcast"

# Example: Thailand bounding box
DEFAULT_LAT = 13.7563
DEFAULT_LON = 100.5018

# API Token (replace with your actual token)
TMD_API_TOKEN = st.secrets["TMD_API_TOKEN"] if "TMD_API_TOKEN" in st.secrets else ""

@st.cache_data(ttl=3600, show_spinner=False)
def get_hourly_forecast(lat=DEFAULT_LAT, lon=DEFAULT_LON):
    """Get 72-hour hourly forecast from TMD API."""
    params = {
        "uid": TMD_API_TOKEN,
        "lat": lat,
        "lon": lon
    }
    try:
        response = requests.get(TMD_HOURLY_API, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"⚠️ Could not fetch hourly forecast: {e}")
        return None

@st.cache_data(ttl=7200, show_spinner=False)
def get_daily_forecast(lat=DEFAULT_LAT, lon=DEFAULT_LON):
    """Get 10-day daily forecast from TMD API."""
    params = {
        "uid": TMD_API_TOKEN,
        "lat": lat,
        "lon": lon
    }
    try:
        response = requests.get(TMD_DAILY_API, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"⚠️ Could not fetch daily forecast: {e}")
        return None

@st.cache_data(ttl=900, show_spinner=False)
def get_nowcast(lat=DEFAULT_LAT, lon=DEFAULT_LON):
    """Get short-term nowcast (next 6 hours) from TMD API."""
    params = {
        "uid": TMD_API_TOKEN,
        "lat": lat,
        "lon": lon
    }
    try:
        response = requests.get(TMD_NOWCAST_API, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"⚠️ Could not fetch nowcast: {e}")
        return None

