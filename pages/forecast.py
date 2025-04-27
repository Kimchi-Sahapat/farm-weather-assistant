# 📈 Forecast - Weather Forecast and Rain Radar Page

import streamlit as st
import pandas as pd
from modules.tmd_api import fetch_daily_forecast, fetch_radar_image
from modules.gps_helper import auto_detect_location, manual_select_location
import folium
from streamlit_folium import st_folium

# 🗺️ Language selection (from main app)
lang = st.session_state.get('lang', 'English')
TEXTS = st.session_state.get('TEXTS', {})

# 🌧️ Rain Radar and Location
st.title("📈 " + TEXTS[lang]["forecast_title"])

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📍 Location Detection")

    gps_mode = st.radio("Select Mode:", ["📡 Auto Detect", "🗺️ Manual Select"], index=0)

    if gps_mode == "📡 Auto Detect":
        location_data = auto_detect_location()
        if location_data:
            lat, lon = map(float, location_data['loc'].split(','))
            city = location_data.get('city', 'Unknown')
            st.success(f"📍 Detected: {city}")
        else:
            st.warning("⚠️ Auto-detection failed. Please select manually.")
            lat, lon, city = manual_select_location()
    else:
        lat, lon, city = manual_select_location()

    st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))

with col2:
    st.markdown(f"### 🌧️ {TEXTS[lang]['radar_title']}")
    m = folium.Map(location=[lat, lon], zoom_start=6)
    folium.raster_layers.TileLayer(
        tiles="https://hpc.tmd.go.th/radar/Composite_SRI/{z}/{x}/{y}.png",
        attr="TMD Radar",
        name="Rain Radar",
        opacity=0.6,
    ).add_to(m)
    st_folium(m, height=350, width=450)

# 🔮 Forecast Section
st.divider()
st.subheader("📅 7-Day Forecast from TMD")

forecast_data = fetch_daily_forecast(lat, lon)

if forecast_data:
    forecast_list = []
    for item in forecast_data[:7]:
        forecast_list.append({
            "Date": item['Date'],
            "Temp Max (°C)": item['MaxTemperature'],
            "Temp Min (°C)": item['MinTemperature'],
            "Rain (%)": item['Rainfall'],
            "Weather": item['WeatherDescriptionTH'] if lang == "ภาษาไทย" else item['WeatherDescription']
        })

    forecast_df = pd.DataFrame(forecast_list)
    st.dataframe(forecast_df, use_container_width=True)

    # 🛑 Risk Color Bar
    st.divider()
    st.subheader("🚦 Rain Risk Timeline")

    risk_colors = []
    for rain in forecast_df['Rain (%)']:
        if rain >= 80:
            risk_colors.append("🔴 Very High")
        elif rain >= 50:
            risk_colors.append("🟠 High")
        elif rain >= 20:
            risk_colors.append("🟡 Moderate")
        else:
            risk_colors.append("🟢 Low")

    risk_df = pd.DataFrame({
        "Date": forecast_df['Date'],
        "Rain Chance (%)": forecast_df['Rain (%)'],
        "Risk Level": risk_colors
    })

    st.dataframe(risk_df, use_container_width=True)

else:
    st.warning("⚠️ Could not fetch forecast data. Please check API credentials or network.")

# End of Forecast Page
