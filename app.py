# 🌾 Farm Weather Assistant - Ultra Final app.py (Part 1)

from modules.gps_helper import auto_detect_location, manual_select_location
import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
import requests
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import os

# 📋 Streamlit page config
st.set_page_config(page_title="Farm Weather Assistant", page_icon="🌾", layout="wide")

# 🌍 Language and Theme Selection
with st.sidebar:
    lang = st.radio("🌐 Language / ภาษา", ("English", "ภาษาไทย"))
    theme = st.radio("🎨 Theme Mode", ("🌞 Light", "🌙 Dark"))
if theme == "🌙 Dark":
    st.markdown("""
        <style>
        body {
            background-color: #0E1117;
            color: #FAFAFA;
        }
        </style>
    """, unsafe_allow_html=True)

# ✅ Your TMD API credentials
UID = "u68sahapat"
UKEY = "8aa48a692a260d6f2319036fa75298cf"

# 🌎 Auto Detect Location
st.divider()
st.subheader("📍 My Location and Rain Radar")

col1, col2 = st.columns(2)

# --- Column 1: GPS Auto-detect and Manual Fallback
with col1:
    gps_mode = st.radio("Location Mode", ("📡 Auto Detect", "🗺️ Manual Select"), index=0)

    if gps_mode == "📡 Auto Detect":
        location = auto_detect_location()
        if location and 'loc' in location:
            lat, lon = map(float, location['loc'].split(","))
            st.success(f"📍 Detected: {location.get('city', 'Unknown')}, {location.get('region', '')}")
        else:
            st.warning("⚠️ Auto-detect failed. Please select manually.")
            lat, lon = manual_select_location()
    else:
        lat, lon = manual_select_location()

with col2:
    m = folium.Map(location=[lat, lon], zoom_start=6)
    folium.raster_layers.TileLayer(
        tiles="https://radar.tmd.go.th/Composite_SRI/{z}/{x}/{y}.png",
        attr="TMD Radar",
        name="Rain Radar",
        opacity=0.5,
    ).add_to(m)
    st_folium(m, width=400, height=350)

# 🌏 Text Dictionaries (English/Thai)
TEXTS = {
    "English": {
        "upload_title": "Upload your weather station file (.csv or .xls)",
        "select_crop": "Select Your Crop",
        "weather_summary": "Today's Farm Weather Summary",
        "chat_title": "Chat with Your Farm Data",
        "trends_title": "Weather Trends",
        "forecast_title": "Weather Forecast (TMD API)",
        "radar_title": "Rain Radar Map",
        "reference_title": "Reference Values and Assumptions",
        "rainfall_today": "Rainfall Today",
        "avg_temp_today": "Avg Temp Today",
        "min_humidity_today": "Min Humidity",
        "gdd_today": "GDD Today",
        "gdd_accumulated": "Accumulated GDD",
        "smart_alerts": "🌟 Smart Farm Alerts",
        "weekly_plan": "📅 Weekly Farm Planner",
        "location_detected": "Location Detected",
        "location_not_detected": "Could not auto-detect location. Please select manually.",
    },
    "ภาษาไทย": {
        "upload_title": "อัปโหลดไฟล์สถานีอากาศ (.csv หรือ .xls)",
        "select_crop": "เลือกชนิดพืช",
        "weather_summary": "สรุปอากาศฟาร์มวันนี้",
        "chat_title": "พูดคุยกับข้อมูลฟาร์มของคุณ",
        "trends_title": "แนวโน้มสภาพอากาศ",
        "forecast_title": "พยากรณ์อากาศ (TMD API)",
        "radar_title": "แผนที่เรดาร์ฝน",
        "reference_title": "ข้อมูลอ้างอิง",
        "rainfall_today": "ปริมาณฝนวันนี้",
        "avg_temp_today": "อุณหภูมิเฉลี่ยวันนี้",
        "min_humidity_today": "ความชื้นต่ำสุด",
        "gdd_today": "GDD วันนี้",
        "gdd_accumulated": "GDD สะสม",
        "smart_alerts": "🌟 การแจ้งเตือนอัจฉริยะ",
        "weekly_plan": "📅 แผนงานฟาร์มประจำสัปดาห์",
        "location_detected": "ตรวจพบตำแหน่งที่ตั้ง",
        "location_not_detected": "ไม่สามารถตรวจจับตำแหน่งอัตโนมัติ กรุณาเลือกเอง",
    }
}

# 🗺️ Sidebar Navigation
with st.sidebar:
    st.markdown("### 🌾 Farm Weather Assistant")
    st.divider()
    page = st.radio(
        "📂 Navigation Menu",
        ("📊 Dashboard", "📈 Forecast", "📖 Reference"),
        index=0
    )
    st.divider()
    st.caption("🌾 Powered by Farm Weather Assistant")


# 📦 Pest and Crop Databases
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
    "ทุเรียน (Durian)": 15,
    "ข้าวโพด (Maize)": 10,
    "มะม่วง (Mango)": 13,
    "มันสำปะหลัง (Cassava)": 8,
    "ข้าว (Rice)": 8,
    "ลิ้นจี่ (Lychee)": 7
}

# 📥 Upload Farm Weather Data
if page == "📊 Dashboard":
    st.title("📊 " + TEXTS[lang]["upload_title"])

    uploaded_file = st.file_uploader(TEXTS[lang]['upload_title'], type=["csv", "xls"])

    if uploaded_file is not None:
        try:
            weather_df = pd.read_csv(uploaded_file, parse_dates=["Date/Time"])
            st.success("✅ CSV file loaded!")
        except Exception:
            try:
                file_bytes = uploaded_file.read()
                if b"<?xml" in file_bytes[:10]:
                    root = ET.fromstring(file_bytes)
                    namespace = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}
                    table = root.find(".//ss:Table", namespace)
                    data = []
                    for row in table.findall(".//ss:Row", namespace):
                        data.append([cell.find(".//ss:Data", namespace).text if cell.find(".//ss:Data", namespace) is not None else None for cell in row.findall(".//ss:Cell", namespace)])
                    headers = [h if h else d for h, d in zip(data[0], data[1])]
                    df_data = data[2:]
                    weather_df = pd.DataFrame(df_data, columns=headers)
                    weather_df.rename(columns={weather_df.columns[0]: "Date/Time"}, inplace=True)
                    weather_df["Date/Time"] = pd.to_datetime(weather_df["Date/Time"], errors="coerce")
                    for col in weather_df.columns[1:]:
                        weather_df[col] = pd.to_numeric(weather_df[col], errors="coerce")
                    st.success("✅ XML XLS file loaded!")
                else:
                    uploaded_file.seek(0)
                    weather_df = pd.read_excel(uploaded_file, engine="openpyxl")
                    weather_df["Date/Time"] = pd.to_datetime(weather_df["Date/Time"], errors="coerce")
                    st.success("✅ XLS file loaded!")
            except Exception as e:
                st.error(f"❌ Error reading file: {e}")
                weather_df = None
    else:
        weather_df = None

    # 📋 If Data Available
    if weather_df is not None:

        # 🌱 Crop Selection
        st.subheader(f"🌱 {TEXTS[lang]['select_crop']}")
        selected_crop = st.selectbox("", list(CROP_BASE_TEMPS.keys()))
        base_temp = CROP_BASE_TEMPS[selected_crop]

        # 🌤️ Today's Summary
        st.divider()
        st.subheader(f"🌞 {TEXTS[lang]['weather_summary']}")
        today = datetime.today().date()
        today_data = weather_df[weather_df["Date/Time"].dt.date == today]

        if not today_data.empty:
            rainfall_today = today_data['Precipitation [mm] (avg)'].sum() if 'Precipitation [mm] (avg)' in today_data.columns else None
            avg_temp_today = today_data['HC Air temperature [°C] (avg)'].mean() if 'HC Air temperature [°C] (avg)' in today_data.columns else None
            min_humid_today = today_data['HC Relative humidity [%] (min)'].min() if 'HC Relative humidity [%] (min)' in today_data.columns else None

            # 🌡️ GDD calculation
            if "HC Air temperature [°C] (max)" in today_data.columns and "HC Air temperature [°C] (min)" in today_data.columns:
                gdd_today = ((today_data["HC Air temperature [°C] (max)"].max() + today_data["HC Air temperature [°C] (min)"].min()) / 2) - base_temp
            elif avg_temp_today is not None:
                gdd_today = avg_temp_today - base_temp
            else:
                gdd_today = 0

            gdd_today = gdd_today if gdd_today > 0 else 0

            # ✨ Daily Summary Cards
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🌧️ " + TEXTS[lang]["rainfall_today"], f"{rainfall_today:.1f} mm" if rainfall_today else "N/A")
            with col2:
                st.metric("🌡️ " + TEXTS[lang]["avg_temp_today"], f"{avg_temp_today:.1f} °C" if avg_temp_today else "N/A")
            with col3:
                st.metric("💧 " + TEXTS[lang]["min_humidity_today"], f"{min_humid_today:.1f} %" if min_humid_today else "N/A")

            st.divider()

            # 🌟 Smart Alerts
            st.subheader(TEXTS[lang]["smart_alerts"])
            if rainfall_today and rainfall_today > 20:
                st.warning("🌧️ Heavy Rain Alert! Possible waterlogging. Check drainage systems.")
            if avg_temp_today and avg_temp_today > 35:
                st.error("🔥 Heat Stress Risk! Monitor water and shade management.")
            if min_humid_today and min_humid_today < 30:
                st.info("💨 Dry Air Warning. Increased pest risk. Inspect crops frequently.")

        else:
            st.info("ℹ️ No weather data recorded for today.")

# 🌦️ Rain Radar + My Location
st.divider()
st.subheader("🌧️ " + TEXTS[lang]["radar_title"])

col1, col2 = st.columns(2)

with col1:
    st.components.v1.iframe(
        "https://www.tmd.go.th/en/weather-radar",
        height=400,
        scrolling=True
    )

with col2:
    st.markdown("### 📍 " + TEXTS[lang]["location_detected"])
    lat, lon, city = auto_detect_location()

    if lat is None or lon is None:
        st.warning(f"⚠️ {TEXTS[lang]['location_not_detected']}")
        lat, lon, city = manual_select_location()
    else:
        st.success(f"📍 {city}")

    st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))

# 🌦️ Forecast Section
st.divider()
st.subheader("📈 " + TEXTS[lang]["forecast_title"])

UID = "u68sahapat"
UKEY = "8aa48a692a260d6f2319036fa75298cf"

params = {
    "uid": UID,
    "ukey": UKEY,
    "lat": lat,
    "lon": lon
}

forecast_url = "https://data.tmd.go.th/nwpapi/v1/forecast/location/daily"

try:
    forecast_response = requests.get(forecast_url, params=params, timeout=10)
    forecast_response.raise_for_status()
    forecast_data = forecast_response.json().get('WeatherForecasts', [])

    if forecast_data:
        forecast_list = []
        for entry in forecast_data:
            forecast_list.append({
                "Datetime": entry['DateTime'],
                "Temperature (°C)": entry['Temperature']['Value'],
                "Rain (%)": entry['Rain']['Value'],
                "Wind (km/h)": entry['WindSpeed']['Value'],
                "Weather": entry['WeatherDescriptionTH'] if lang == "ภาษาไทย" else entry['WeatherDescription']
            })

        forecast_df = pd.DataFrame(forecast_list)

        for idx, row in forecast_df.head(7).iterrows():
            st.info(f"**{row['Datetime']}**\n\n🌡️ {row['Temperature (°C)']} °C | 🌧️ {row['Rain (%)']}% chance | 🌬️ {row['Wind (km/h)']} km/h\n\n{row['Weather']}")
    else:
        st.warning("⚠️ No forecast data received.")
except Exception as e:
    st.warning(f"⚠️ Could not fetch forecast: {e}")

# 🔥 Risk Timeline Color Bar
st.divider()
st.subheader("🚦 Risk Timeline (Next 7 Days)")

if 'forecast_df' in locals() and not forecast_df.empty:
    risk_colors = []
    for rain in forecast_df['Rain (%)'].head(7):
        if rain >= 80:
            risk_colors.append("🔴 Very High")
        elif rain >= 50:
            risk_colors.append("🟠 High")
        elif rain >= 20:
            risk_colors.append("🟡 Moderate")
        else:
            risk_colors.append("🟢 Low")

    risk_df = pd.DataFrame({
        "Date": forecast_df['Datetime'].head(7),
        "Rain Chance (%)": forecast_df['Rain (%)'].head(7),
        "Risk Level": risk_colors
    })

    st.dataframe(risk_df)
else:
    st.info("No forecast data to generate Risk Timeline.")


# 🌱 Smart Fertilizer and Pest Advisory
st.divider()
st.subheader("🧠 " + TEXTS[lang]["smart_alerts"])

advisory_msgs = []

if 'forecast_df' in locals() and not forecast_df.empty:
    if forecast_df['Rain (%)'].mean() > 60:
        advisory_msgs.append("🌧️ Frequent rains expected. Delay fertilizer application.")
    elif forecast_df['Rain (%)'].mean() < 20:
        advisory_msgs.append("🌞 Dry conditions ahead. Irrigate before fertilizing.")
    else:
        advisory_msgs.append("✅ Good weather for fertilizer application.")

    if forecast_df['Rain (%)'].max() > 80:
        advisory_msgs.append("🐛 Pest outbreak risk due to humidity. Monitor crops closely.")
    elif forecast_df['Temperature (°C)'].mean() > 32:
        advisory_msgs.append("🔥 Hot weather alert: Monitor mites and heat-stress signs.")

    for msg in advisory_msgs:
        st.success(msg)
else:
    st.info("ℹ️ No forecast data available for advisory.")


# Pest Outbreak Risk
if forecast_df['Rain (%)'].max() > 80:
    advisory_msgs.append("🐛 High risk of pest outbreaks due to humidity. Monitor for fungi and insects closely.")
elif forecast_df['Temperature (°C)'].mean() > 32:
    advisory_msgs.append("🔥 Hot weather alert: Monitor for mites and heat-stress pests.")

# GDD Status Advisory
if last_gdd is not None and last_gdd > 500:
    advisory_msgs.append("🎯 Accumulated GDD reached! Consider shifting crop stage or preparing for harvest.")

for msg in advisory_msgs:
    st.success(msg)

# 📅 Weekly Farm Task Planner
st.divider()
st.subheader("📅 " + TEXTS[lang]["weekly_plan"])

if 'forecast_df' in locals() and not forecast_df.empty:
    today = datetime.now()
    planner_tasks = []

    for i in range(7):
        future_day = today + timedelta(days=i)
        rain_chance = forecast_df.iloc[i]['Rain (%)'] if i < len(forecast_df) else 0
        task = ""

        if rain_chance >= 70:
            task = "🌧️ Avoid spraying, delay fieldwork, inspect fields."
        elif rain_chance <= 20:
            task = "☀️ Good day for fertilizing, planting, or soil work."
        else:
            task = "🌤️ Moderate risk. Check morning weather."

        planner_tasks.append({
            "Date": future_day.strftime("%a %d %b"),
            "Recommended Task": task
        })

    task_df = pd.DataFrame(planner_tasks)
    st.dataframe(task_df)
else:
    st.info("ℹ️ No forecast data for weekly planner.")

# 🎨 Theme Mode
if 'theme_mode' not in st.session_state:
    st.session_state.theme_mode = 'light'

theme_mode = st.sidebar.radio(
    "🎨 Theme Mode",
    ["🌞 Light", "🌙 Dark"],
    index=0 if st.session_state.theme_mode == 'light' else 1
)
st.session_state.theme_mode = theme_mode

if theme_mode == "🌙 Dark":
    st.markdown(
        """
        <style>
        body {
            background-color: #0E1117;
            color: #FAFAFA;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
