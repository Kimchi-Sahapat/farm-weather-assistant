# forecast.py placeholder
import streamlit as st
import folium
from streamlit_folium import st_folium
from modules.tmd_api import fetch_forecast_data, fetch_radar_image

# --- Sidebar ---
st.title("🌦️ Forecast Dashboard")

# --- User Location or Input ---
st.subheader("📍 Location for Forecast")
lat = st.number_input("Latitude", value=13.736717)
lon = st.number_input("Longitude", value=100.523186)

# --- Fetch Forecast Data ---
forecast = fetch_forecast_data(lat, lon)
radar_url = fetch_radar_image()

# --- Create Folium Map ---
m = folium.Map(location=[lat, lon], zoom_start=8)

# Layer: Your location
folium.Marker([lat, lon], tooltip="Your Farm Location").add_to(m)

# Layer: Radar Image
if radar_url:
    folium.raster_layers.ImageOverlay(
        image=radar_url,
        bounds=[[5, 97], [20, 105]],  # Thailand rough bounds
        opacity=0.4,
    ).add_to(m)

# --- Show Map ---
st_folium(m, width=700, height=500)

# --- Show Forecast Info ---
if forecast:
    st.subheader("📋 Hourly Forecast (Next 24 Hours)")
    for hour in forecast.get('hourly', [])[:24]:
        st.write(f"🕒 {hour['time']}: 🌡️ {hour['temp']}°C | 💧 {hour['humidity']}% | 🌧️ {hour['rain']}% chance rain")
else:
    st.warning("⚠️ Forecast data is not available.")
