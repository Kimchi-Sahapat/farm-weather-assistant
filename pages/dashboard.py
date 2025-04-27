import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
from modules.weather_loader import load_weather_file
from modules.smart_alert import generate_smart_alerts
from modules.task_planner import generate_weekly_tasks

# 📋 Upload Section
st.title("📊 Farm Dashboard")

uploaded_file = st.file_uploader("📂 Upload Weather Station File", type=["csv", "xls"])

if uploaded_file:
    weather_df = load_weather_file(uploaded_file)

    if weather_df is not None:
        st.success("✅ Weather data loaded successfully!")

        # 🌱 Select Crop
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

        # 🌞 Today's Summary
        st.divider()
        st.subheader("🌞 Today's Weather Summary")

        today = datetime.today().date()
        today_data = weather_df[weather_df['Date/Time'].dt.date == today]

        if not today_data.empty:
            col1, col2, col3 = st.columns(3)

            rainfall = today_data['Precipitation [mm] (avg)'].sum() if 'Precipitation [mm] (avg)' in today_data else None
            avg_temp = today_data['HC Air temperature [°C] (avg)'].mean() if 'HC Air temperature [°C] (avg)' in today_data else None
            min_humidity = today_data['HC Relative humidity [%] (min)'].min() if 'HC Relative humidity [%] (min)' in today_data else None

            with col1:
                st.metric("🌧️ Rainfall Today", f"{rainfall:.1f} mm" if rainfall else "N/A")
            with col2:
                st.metric("🌡️ Avg Temp Today", f"{avg_temp:.1f} °C" if avg_temp else "N/A")
            with col3:
                st.metric("💧 Min Humidity", f"{min_humidity:.1f} %" if min_humidity else "N/A")
        else:
            st.info("ℹ️ No data recorded for today.")

        # 🌟 Smart Alerts
        st.divider()
        st.subheader("🌟 Smart Farm Alerts")
        if rainfall or avg_temp or min_humidity:
            smart_alerts = generate_smart_alerts(rainfall, avg_temp, min_humidity)
            for alert in smart_alerts:
                st.warning(alert)

        # 📈 Weather Trend Chart
        st.divider()
        st.subheader("📈 Weather Trend (Past 30 Days)")

        past_30_days = weather_df[weather_df['Date/Time'] > datetime.now() - timedelta(days=30)]

        if not past_30_days.empty:
            past_30_days['Rainfall_MA'] = past_30_days['Precipitation [mm] (avg)'].rolling(window=3).mean()
            past_30_days['Temperature_MA'] = past_30_days['HC Air temperature [°C] (avg)'].rolling(window=3).mean()

            col1, col2 = st.columns(2)
            with col1:
                st.line_chart(past_30_days[['Date/Time', 'Rainfall_MA']].set_index('Date/Time'))
            with col2:
                st.line_chart(past_30_days[['Date/Time', 'Temperature_MA']].set_index('Date/Time'))
        else:
            st.info("ℹ️ No recent data to show trends.")

        # 📅 Weekly Farm Planner
        st.divider()
        st.subheader("📅 Weekly Farm Planner")

        weekly_plan = generate_weekly_tasks()
        st.dataframe(weekly_plan)

else:
    st.info("📂 Please upload a weather station file to start.")
