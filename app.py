# Full app.py for Farm Weather Assistant (optional columns version)

import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import os

# Streamlit page config
st.set_page_config(page_title="Farm Weather Assistant", page_icon="🌾", layout="wide")

# Pest and Crop Databases
PEST_DATABASE = {
    "เพลี้ยไฟ": {"Topt_min": 28, "Topt_max": 32, "Note": "Sensitive to light and low humidity."},
    "เพลี้ยแป้ง": {"Topt_min": 25, "Topt_max": 30, "Note": "Prefers stable climates."},
    "ไรแดง": {"Topt_min": 30, "Topt_max": 32, "Note": "Outbreaks in dry air."},
    "หนอนเจาะผลไม้": {"Topt_min": 28, "Topt_max": 30, "Note": "Very important in mango/durian."},
    "ด้วงวงมะม่วง": {"Topt_min": 30, "Topt_max": 30, "Note": "Moves quickly during hot season."},
    "หนอนกระทู้": {"Topt_min": 27, "Topt_max": 30, "Note": "Life cycle speed up."},
    "แมลงวันผลไม้": {"Topt_min": 27, "Topt_max": 30, "Note": "Lays eggs during early ripening."}
}

CROP_BASE_TEMPS = {
    "ข้าวโพด (Maize)": 10,
    "ทุเรียน (Durian)": 15,
    "มะม่วง (Mango)": 13,
    "มันสำปะหลัง (Cassava)": 8,
    "ข้าว (Rice)": 8,
    "ลิ้นจี่ (Lychee)": 7
}

# (Helper functions unchanged)
# (Uploading section unchanged)

if weather_df is not None:
    # Crop Selection
    st.divider()
    st.subheader("🌱 Select Your Crop")
    selected_crop = st.selectbox("เลือกชนิดพืชที่ปลูก:", options=list(CROP_BASE_TEMPS.keys()), index=0)
    base_temp = CROP_BASE_TEMPS[selected_crop]
    st.success(f"✅ Selected Crop: {selected_crop} (Base Temperature = {base_temp}°C)")

    # Daily Farm Summary
    st.divider()
    st.subheader("🌞 Today's Farm Weather Summary")
    today = datetime.today().date()
    today_data = weather_df[weather_df['Date/Time'].dt.date == today]

    if not today_data.empty:
        rainfall_today = today_data['Precipitation [mm] (avg)'].sum() if 'Precipitation [mm] (avg)' in today_data.columns else None
        avg_temp_today = today_data['HC Air temperature [°C] (avg)'].mean() if 'HC Air temperature [°C] (avg)' in today_data.columns else None
        min_humid_today = today_data['HC Relative humidity [%] (min)'].min() if 'HC Relative humidity [%] (min)' in today_data.columns else None

        # GDD Today calculation fallback
        if 'HC Air temperature [°C] (max)' in today_data.columns and 'HC Air temperature [°C] (min)' in today_data.columns:
            today_max = today_data['HC Air temperature [°C] (max)'].max()
            today_min = today_data['HC Air temperature [°C] (min)'].min()
            gdd_today = ((today_max + today_min) / 2) - base_temp
        elif avg_temp_today is not None:
            gdd_today = avg_temp_today - base_temp
        else:
            gdd_today = None

        gdd_today = gdd_today if (gdd_today is not None and gdd_today > 0) else 0

        reset_start_date = datetime(2024, 12, 1).date()
        gdd_df = calculate_gdd(weather_df, base_temperature=base_temp, reset_date=reset_start_date)
        last_gdd = gdd_df['Accumulated GDD'].iloc[-1] if 'Accumulated GDD' in gdd_df.columns else None

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🌧️ Rainfall Today", f"{rainfall_today:.2f} mm" if rainfall_today is not None else "Data Not Found")
        with col2:
            st.metric("🌡️ Avg Temp Today", f"{avg_temp_today:.2f} °C" if avg_temp_today is not None else "Data Not Found")
        with col3:
            st.metric("💧 Min Humidity", f"{min_humid_today:.2f} %" if min_humid_today is not None else "Data Not Found")

        col4, col5 = st.columns(2)
        with col4:
            st.metric("🌱 GDD Today", f"{gdd_today:.2f}°C-days" if gdd_today is not None else "Data Not Found")
        with col5:
            st.metric("🌱 Accumulated GDD", f"{last_gdd:.2f}°C-days" if last_gdd is not None else "Data Not Found")

        GDD_TARGET = 500
        if last_gdd is not None:
            if last_gdd >= GDD_TARGET:
                st.success(f"🎯 GDD Target Reached! (Target: {GDD_TARGET}°C-days)")
            else:
                remaining = GDD_TARGET - last_gdd
                st.info(f"🌱 {remaining:.2f}°C-days remaining to reach {GDD_TARGET}°C-days.")
    else:
        st.info("ℹ️ No data recorded for today.")

# Chat Section
if weather_df is not None:
    st.subheader("💬 Chat with Your Farm Data")
    if 'history' not in st.session_state:
        st.session_state['history'] = []

    for message in st.session_state['history']:
        align = "user" if message['role'] == "user" else "assistant"
        with st.chat_message(align):
            st.markdown(message['content'])

    user_message = st.chat_input("Ask anything about rainfall, temperature, farming advice, or pest risks!")

    if user_message:
        st.session_state['history'].append({"role": "user", "content": user_message})

        with st.chat_message("user"):
            st.markdown(user_message)

        response = "🤔 Sorry, I didn't understand. Try asking about rainfall, April temperature, farming advice, or pest risks."
        user_lower = user_message.lower()

        if 'rain' in user_lower and ('last month' in user_lower or 'rainfall' in user_lower):
            rain = get_total_rainfall_last_month(weather_df)
            response = f"🌧️ **Total rainfall last month: {rain:.2f} mm**."

        elif 'april' in user_lower and ('hotter' in user_lower or 'temperature' in user_lower):
            this_year, last_year = compare_april_temperature(weather_df)
            if pd.isna(this_year) or pd.isna(last_year):
                response = "⚠️ Not enough data available for April temperature comparison."
            else:
                response = f"🌡️ **April {datetime.today().year}: {this_year:.2f} °C**\n🌡️ **April {datetime.today().year-1}: {last_year:.2f} °C**."

        elif any(word in user_lower for word in ['advice', 'fertilize', 'recommend', 'action', 'farming']):
            recommendation = recommend_agriculture_action(weather_df)
            response = recommendation

        elif 'pest' in user_lower or 'ศัตรูพืช' in user_lower or 'แมลง' in user_lower:
            response = check_pest_risks(weather_df)

        with st.chat_message("assistant"):
            st.markdown(response)

        st.session_state['history'].append({"role": "assistant", "content": response})

# 📈 Weather Trend Charts with Time Filter + Moving Average

st.divider()
st.subheader("📈 Weather Trends")

# 📅 Allow user to choose time range
time_range = st.selectbox(
    "Select time range:",
    ("Last 7 Days", "Last 30 Days", "Last 90 Days", "Last 365 Days")
)

# Set days back based on choice
days_back = {
    "Last 7 Days": 7,
    "Last 30 Days": 30,
    "Last 90 Days": 90,
    "Last 365 Days": 365
}[time_range]

# Filter data
if weather_df is not None:
    filtered_data = weather_df[weather_df['Date/Time'] > datetime.now() - timedelta(days=days_back)]

    # Calculate Moving Averages
    filtered_data['Rainfall_MA'] = filtered_data['Precipitation [mm] (avg)'].rolling(window=3).mean()
    filtered_data['Temperature_MA'] = filtered_data['HC Air temperature [°C] (avg)'].rolling(window=3).mean()
    filtered_data['Humidity_MA'] = filtered_data['HC Relative humidity [%] (min)'].rolling(window=3).mean()

    # Layout charts
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🌧️ Rainfall (Smoothed)")
        rain_chart = filtered_data[['Date/Time', 'Rainfall_MA']].dropna()
        rain_chart = rain_chart.set_index('Date/Time')
        st.line_chart(rain_chart)

    with col2:
        st.markdown("### 🌡️ Temperature (Smoothed)")
        temp_chart = filtered_data[['Date/Time', 'Temperature_MA']].dropna()
        temp_chart = temp_chart.set_index('Date/Time')
        st.line_chart(temp_chart)

    with col3:
        st.markdown("### 💧 Humidity (Smoothed)")
        humid_chart = filtered_data[['Date/Time', 'Humidity_MA']].dropna()
        humid_chart = humid_chart.set_index('Date/Time')
        st.line_chart(humid_chart)
