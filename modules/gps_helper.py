# modules/gps_helper.py

import requests
import streamlit as st

# 🌍 Auto-detect location based on IP address
def auto_detect_location():
    try:
        response = requests.get("https://ipinfo.io/json", timeout=5)
        data = response.json()
        loc = data.get("loc", None)  # Format: "latitude,longitude"
        if loc:
            lat, lon = map(float, loc.split(","))
            city = data.get("city", "Unknown")
            return lat, lon, city
        else:
            return None, None, None
    except Exception as e:
        st.warning(f"⚠️ Location auto-detection failed: {e}")
        return None, None, None

# 🗺️ Manual location selection fallback
def manual_select_location():
    st.info("📍 Please manually select your farm location.")
    col1, col2 = st.columns(2)
    with col1:
        lat = st.number_input("Latitude", value=13.736717, format="%.6f")
    with col2:
        lon = st.number_input("Longitude", value=100.523186, format="%.6f")
    city = "Manual Selection"
    return lat, lon, city
