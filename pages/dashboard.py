# pages/dashboard.py

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
from modules.weather_loader import load_weather_file

# 📦 Helper function for weather file upload
def load_weather_file(uploaded_file):
    try:
        df = pd.read_csv(uploaded_file, parse_dates=["Date/Time"])
        return df
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
                df = pd.DataFrame(df_data, columns=headers)
                df.rename(columns={df.columns[0]: "Date/Time"}, inplace=True)
                df["Date/Time"] = pd.to_datetime(df["Date/Time"], errors="coerce")
                for col in df.columns[1:]:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                return df
            else:
                uploaded_file.seek(0)
                df = pd.read_excel(uploaded_file, engine="xlrd")
                df["Date/Time"] = pd.to_datetime(df["Date/Time"], errors="coerce")
                return df
        except Exception as e:
            st.error(f"❌ Error loading file: {e}")
            return None

# 📋 Dashboard Main Logic
def show_dashboard(TEXTS, CROP_BASE_TEMPS):
    st.title(f"📊 {TEXTS['upload_title']}")

    uploaded_file = st.file_uploader(TEXTS[lang]['upload_title'], type=["csv", "xls"])

if uploaded_file:
    weather_df = load_weather_file(uploaded_file)
    if weather_df is not None:
        st.success("✅ Weather data loaded successfully!")
            st.dataframe(weather_df.head())
        else:
            return
    else:
        st.info("ℹ️ Please upload a farm weather file.")
        return

    # 🌱 Crop Selection
    st.subheader(f"🌱 {TEXTS['select_crop']}")
    selected_crop = st.selectbox("", list(CROP_BASE_TEMPS.keys()))
    base_temp = CROP_BASE_TEMPS[selected_crop]

    # 🌞 Today's Summary
    st.divider()
    st.subheader(f"🌞 {TEXTS['weather_summary']}")

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
            st.metric("🌧️ " + TEXTS["rainfall_today"], f"{rainfall_today:.1f} mm" if rainfall_today else "N/A")
        with col2:
            st.metric("🌡️ " + TEXTS["avg_temp_today"], f"{avg_temp_today:.1f} °C" if avg_temp_today else "N/A")
        with col3:
            st.metric("💧 " + TEXTS["min_humidity_today"], f"{min_humid_today:.1f} %" if min_humid_today else "N/A")

    else:
        st.info("ℹ️ No weather data recorded for today.")
