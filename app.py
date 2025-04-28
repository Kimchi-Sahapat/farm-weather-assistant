# 📋 Farm Weather Assistant - app.py

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import requests
import folium
from streamlit_folium import st_folium

# Custom modules
from modules.gps_helper import auto_detect_location, manual_select_location
from modules.smart_alert import generate_smart_alerts
from modules.task_planner import generate_task_plan

# ✅ API credentials
UID = "u68sahapat"
UKEY = "8aa48a692a260d6f2319036fa75298cf"

# 📋 Streamlit Page Config
st.set_page_config(page_title="Farm Weather Assistant", page_icon="🌾", layout="wide")

# 🌍 Language and Theme Settings
with st.sidebar:
    lang = st.radio("🌐 Language / ภาษา", ("English", "ภาษาไทย"))
    theme = st.selectbox("🎨 Theme Mode", ("light", "dark"))
    st.session_state.theme_mode = theme

# 🌾 Text Dictionary
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
    }
}

# 📚 Database
CROP_BASE_TEMPS = {
    "ทุเรียน (Durian)": 15,
    "ข้าวโพด (Maize)": 10,
    "มะม่วง (Mango)": 13,
    "มันสำปะหลัง (Cassava)": 8,
    "ข้าว (Rice)": 8,
    "ลิ้นจี่ (Lychee)": 7,
}

# 📋 Sidebar Navigation
with st.sidebar:
    st.markdown("### 🌾 Farm Weather Assistant")
    page = st.radio("", ("📊 Dashboard", "📈 Forecast", "📖 Reference"))
    st.divider()
    st.caption("🌾 Powered by Farm Weather Assistant")
# 📊 Dashboard Page
if page == "📊 Dashboard":
    st.title("📊 " + TEXTS[lang]["upload_title"])

    uploaded_file = st.file_uploader(TEXTS[lang]['upload_title'], type=["csv", "xls"])

    # Load uploaded file
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                weather_df = pd.read_csv(uploaded_file, parse_dates=["Date/Time"])
            else:
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
                else:
                    uploaded_file.seek(0)
                    weather_df = pd.read_excel(uploaded_file, engine="openpyxl")
                    weather_df["Date/Time"] = pd.to_datetime(weather_df["Date/Time"], errors="coerce")

            st.success("✅ Weather file loaded successfully!")

        except Exception as e:
            st.error(f"❌ Error loading file: {e}")
            weather_df = None
    else:
        weather_df = None

    # If weather data is available
    if weather_df is not None:
        # 🌱 Select Crop
        st.subheader(f"🌱 {TEXTS[lang]['select_crop']}")
        selected_crop = st.selectbox("", list(CROP_BASE_TEMPS.keys()))
        base_temp = CROP_BASE_TEMPS[selected_crop]

        # 🌞 Today's Farm Weather Summary
        st.divider()
        st.subheader(f"🌞 {TEXTS[lang]['weather_summary']}")

        today = datetime.today().date()
        today_data = weather_df[weather_df["Date/Time"].dt.date == today]

        if not today_data.empty:
            rainfall_today = today_data.get('Precipitation [mm] (avg)', pd.Series([None])).sum()
            avg_temp_today = today_data.get('HC Air temperature [°C] (avg)', pd.Series([None])).mean()
            min_humid_today = today_data.get('HC Relative humidity [%] (min)', pd.Series([None])).min()

            # GDD Calculation
            if "HC Air temperature [°C] (max)" in today_data.columns and "HC Air temperature [°C] (min)" in today_data.columns:
                gdd_today = ((today_data["HC Air temperature [°C] (max)"].max() + today_data["HC Air temperature [°C] (min)"].min()) / 2) - base_temp
            elif avg_temp_today is not None:
                gdd_today = avg_temp_today - base_temp
            else:
                gdd_today = 0
            gdd_today = gdd_today if gdd_today > 0 else 0

            # Show daily summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🌧️ " + TEXTS[lang]["rainfall_today"], f"{rainfall_today:.1f} mm" if rainfall_today else "N/A")
            with col2:
                st.metric("🌡️ " + TEXTS[lang]["avg_temp_today"], f"{avg_temp_today:.1f} °C" if avg_temp_today else "N/A")
            with col3:
                st.metric("💧 " + TEXTS[lang]["min_humidity_today"], f"{min_humid_today:.1f} %" if min_humid_today else "N/A")

            st.divider()

            # 🌟 Smart Farm Alerts
            st.subheader(TEXTS[lang]["smart_alerts"])

            forecast_points = []
            for _, row in today_data.iterrows():
                forecast_points.append({
                    'rain': row.get('Precipitation [mm] (avg)', 0),
                    'temp': row.get('HC Air temperature [°C] (avg)', 0),
                    'humidity': row.get('HC Relative humidity [%] (avg)', 70)
                })

            alerts = generate_smart_alerts(forecast_points, gdd_today)
            for alert in alerts:
                st.success(alert)

        else:
            st.info("ℹ️ No weather data for today.")
# 📍 Rain Radar and My Location
st.divider()
st.subheader("🌧️ " + TEXTS[lang]["radar_title"])

col1, col2 = st.columns(2)

# --- Rain Radar Map
with col1:
    m = folium.Map(location=[13.736717, 100.523186], zoom_start=6)
    folium.raster_layers.TileLayer(
        tiles="https://radar.tmd.go.th/Composite_SRI/{z}/{x}/{y}.png",
        attr="TMD Radar",
        name="Rain Radar",
        opacity=0.6,
    ).add_to(m)
    st_folium(m, width=400, height=350)

# --- Auto-detect GPS
with col2:
    st.markdown("### 📍 Location Detection")

    gps_mode = st.radio("Choose Location Mode", ["📡 Auto Detect", "🗺️ Manual Select"])

    if gps_mode == "📡 Auto Detect":
        location_info = auto_detect_location()
        if location_info:
            lat, lon = map(float, location_info['loc'].split(','))
            st.success(f"📍 Detected Location: {location_info.get('city', 'Unknown City')}")
        else:
            st.warning("⚠️ Failed to detect automatically. Please select manually.")
            lat, lon = manual_select_location()
    else:
        lat, lon = manual_select_location()

    st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))

# 📈 7-Day Forecast Summary (TMD API)
st.divider()
st.subheader("📈 " + TEXTS[lang]["forecast_title"])

try:
    from modules.tmd_api import fetch_daily_forecast

    forecast_raw = fetch_daily_forecast(lat, lon)

    forecast_data = []
    for item in forecast_raw[:7]:  # limit to 7 days
        forecast_data.append({
            "date": item.get('Date'),
            "temp": item.get('Tmax', None),
            "rain": item.get('Rain', None),
            "desc": item.get('WeatherDescriptionTH') if lang == "ภาษาไทย" else item.get('WeatherDescription')
        })

    forecast_df = pd.DataFrame(forecast_data)

    if not forecast_df.empty:
        for _, row in forecast_df.iterrows():
            st.info(
                f"**{row['date']}**\n\n"
                f"🌡️ Max Temp: {row['temp']} °C\n"
                f"🌧️ Rainfall: {row['rain']} mm\n\n"
                f"{row['desc']}"
            )
    else:
        st.warning("⚠️ No forecast data available.")

except Exception as e:
    st.error(f"❌ Could not load forecast: {e}")

# 🚦 Risk Timeline (Rainfall Focus)
st.divider()
st.subheader("🚦 Risk Timeline (Next 7 Days)")

if not forecast_df.empty:
    risk_levels = []
    for rain in forecast_df['rain']:
        if rain is not None:
            if rain >= 30:
                risk_levels.append("🔴 Very High Risk")
            elif rain >= 10:
                risk_levels.append("🟠 Medium Risk")
            else:
                risk_levels.append("🟢 Low Risk")
        else:
            risk_levels.append("⚪ Unknown")

    timeline_df = pd.DataFrame({
        "Date": forecast_df['date'],
        "Risk Level": risk_levels
    })

    st.dataframe(timeline_df)

# 🧠 Smart Farm Advisory
st.divider()
st.subheader("🧠 Smart Farm Advisory")

from modules.smart_alert import generate_smart_alerts

try:
    forecast_points = []
    for idx, row in forecast_df.iterrows():
        forecast_points.append({
            'rain': row['rain'] if row['rain'] is not None else 0,
            'temp': row['temp'] if row['temp'] is not None else 0,
            'humidity': 70  # fallback (TMD daily forecast may not include humidity)
        })

    advisory_msgs = generate_smart_alerts(forecast_points, last_gdd if 'last_gdd' in globals() else None)

    for msg in advisory_msgs:
        st.success(msg)

except Exception as e:
    st.warning(f"⚠️ Could not generate smart advisory: {e}")

# 📅 Weekly Farm Task Planner
st.divider()
st.subheader(TEXTS[lang]["weekly_plan"])

today = datetime.now()
planner_tasks = []

for i in range(7):
    future_day = today + timedelta(days=i)
    rain_forecast = forecast_df.iloc[i]['rain'] if i < len(forecast_df) else None

    if rain_forecast is None:
        task = "❓ Weather data not available."
    elif rain_forecast >= 30:
        task = "🌧️ Heavy rain expected. Delay heavy field work, inspect drainage."
    elif rain_forecast >= 10:
        task = "🌦️ Possible showers. Prepare flexible plans."
    else:
        task = "☀️ Dry day. Good for field work, fertilization, or pest management."

    planner_tasks.append({
        "Date": future_day.strftime("%a %d %b"),
        "Recommended Task": task
    })

task_df = pd.DataFrame(planner_tasks)
st.dataframe(task_df)

# 🎨 Light/Dark Mode Polish
theme_mode = st.sidebar.radio("🎨 Theme Mode", ["🌞 Light", "🌙 Dark"], index=0)

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

# 📋 Footer
st.divider()
st.caption("🌾 Powered by Farm Weather Assistant - helping you grow smarter every day.")
