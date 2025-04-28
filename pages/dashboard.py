# /pages/dashboard.py

import streamlit as st
import pandas as pd
from datetime import datetime
from modules.weather_loader import load_weather_file
from modules.smart_alert import generate_alerts

# 🌾 Dashboard Page
st.title("📊 Farm Dashboard")

# 📥 Upload Farm Weather Data
uploaded_file = st.file_uploader("📂 Upload your weather station file (.csv or .xls)", type=["csv", "xls", "xlsx"])

if uploaded_file is not None:
    weather_df = load_weather_file(uploaded_file)

    if weather_df is not None:
        st.success("✅ Weather data loaded successfully!")
        st.info(f"📚 Available Columns: {', '.join(weather_df.columns)}")

        st.divider()

        # 🌱 Crop Selection
        crop_options = {
            "ทุเรียน (Durian)": 15,
            "ข้าวโพด (Maize)": 10,
            "มะม่วง (Mango)": 13,
            "มันสำปะหลัง (Cassava)": 8,
            "ข้าว (Rice)": 8,
            "ลิ้นจี่ (Lychee)": 7,
        }

        selected_crop = st.selectbox("🌱 Select Your Crop", list(crop_options.keys()))
        base_temp = crop_options[selected_crop]

        # 🌤️ Today's Weather Summary
        st.subheader("🌞 Today's Farm Weather Summary")
        today = datetime.today().date()
        today_data = weather_df[weather_df["Date/Time"].dt.date == today]

        if not today_data.empty:
            rainfall_today = today_data.get('Precipitation [mm] (avg)', pd.Series()).sum()
            avg_temp_today = today_data.get('HC Air temperature [°C] (avg)', pd.Series()).mean()
            min_humid_today = today_data.get('HC Relative humidity [%] (min)', pd.Series()).min()

            if "HC Air temperature [°C] (max)" in today_data.columns and "HC Air temperature [°C] (min)" in today_data.columns:
                gdd_today = ((today_data["HC Air temperature [°C] (max)"].max() + today_data["HC Air temperature [°C] (min)"].min()) / 2) - base_temp
            elif avg_temp_today is not None:
                gdd_today = avg_temp_today - base_temp
            else:
                gdd_today = 0

            gdd_today = max(gdd_today, 0)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🌧️ Rainfall Today", f"{rainfall_today:.2f} mm" if pd.notnull(rainfall_today) else "N/A")
            with col2:
                st.metric("🌡️ Avg Temp Today", f"{avg_temp_today:.2f} °C" if pd.notnull(avg_temp_today) else "N/A")
            with col3:
                st.metric("💧 Min Humidity Today", f"{min_humid_today:.2f} %" if pd.notnull(min_humid_today) else "N/A")

            st.divider()

            # 🌟 Smart Farm Alerts
            st.subheader("🌟 Smart Farm Alerts")
            simulated_forecast = []
            for idx, row in today_data.iterrows():
                simulated_forecast.append({
                    'rain': row.get('Precipitation [mm] (avg)', 0),
                    'temp': row.get('HC Air temperature [°C] (avg)', 0),
                    'humidity': row.get('HC Relative humidity [%] (avg)', 70)
                })

            smart_alerts = generate_alerts(simulated_forecast, gdd_today)

            for alert in smart_alerts:
                if "delay" in alert.lower() or "rain" in alert.lower():
                    st.warning(alert)
                elif "pest" in alert.lower():
                    st.error(alert)
                else:
                    st.success(alert)

        else:
            st.info("ℹ️ No weather data recorded for today.")
    else:
        st.error("❌ Could not load the weather file.")
else:
    st.info("📂 Please upload your weather data file (.csv, .xls)")
