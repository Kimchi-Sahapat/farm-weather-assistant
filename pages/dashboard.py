# 📊 Dashboard - Upload Farm Weather Data and Daily Summary

import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime
from modules.weather_loader import load_weather_file
from modules.smart_alert import generate_smart_alerts
from modules.task_planner import generate_weekly_task_plan

# 🗺️ Language selection (from main app)
lang = st.session_state.get('lang', 'English')
TEXTS = st.session_state.get('TEXTS', {})

# 📥 Upload Weather Station File
st.title("📊 " + TEXTS[lang]["upload_title"])

uploaded_file = st.file_uploader(TEXTS[lang]["upload_title"], type=["csv", "xls"])

if uploaded_file is not None:
    weather_df = load_weather_file(uploaded_file)
    if weather_df is not None:
        st.success("✅ Weather file loaded!")
    else:
        st.error("❌ Failed to load weather file.")
else:
    weather_df = None

# 🌤️ Daily Weather Summary
if weather_df is not None:
    st.divider()
    st.subheader(f"🌞 {TEXTS[lang]['weather_summary']}")

    today = datetime.today().date()
    today_data = weather_df[weather_df["Date/Time"].dt.date == today]

    if not today_data.empty:
        rainfall_today = today_data['Precipitation [mm] (avg)'].sum() if 'Precipitation [mm] (avg)' in today_data.columns else None
        avg_temp_today = today_data['HC Air temperature [°C] (avg)'].mean() if 'HC Air temperature [°C] (avg)' in today_data.columns else None
        min_humid_today = today_data['HC Relative humidity [%] (min)'].min() if 'HC Relative humidity [%] (min)' in today_data.columns else None

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🌧️ " + TEXTS[lang]["rainfall_today"], f"{rainfall_today:.1f} mm" if rainfall_today else "N/A")
        with col2:
            st.metric("🌡️ " + TEXTS[lang]["avg_temp_today"], f"{avg_temp_today:.1f} °C" if avg_temp_today else "N/A")
        with col3:
            st.metric("💧 " + TEXTS[lang]["min_humidity_today"], f"{min_humid_today:.1f} %" if min_humid_today else "N/A")
    else:
        st.info("ℹ️ No weather data recorded for today.")

# 🌟 Smart Farm Alerts
    st.divider()
    st.subheader(f"🌟 {TEXTS[lang]['smart_alerts']}")

    alerts = generate_smart_alerts(weather_df)
    for alert in alerts:
        st.warning(alert)

# 📅 Weekly Task Planner
    st.divider()
    st.subheader(f"📅 {TEXTS[lang]['weekly_plan']}")

    task_plan = generate_weekly_task_plan(weather_df)
    st.dataframe(task_plan, use_container_width=True)

else:
    st.info("📄 Please upload a weather station file to continue.")

# End of Dashboard Page
