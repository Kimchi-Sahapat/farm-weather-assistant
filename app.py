# Full app.py for Farm Weather Assistant (with Welcome Message, Charts Patch, Reference Page)

import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import os

# Streamlit page config
st.set_page_config(page_title="Farm Weather Assistant", page_icon="🌾", layout="wide")

# Set Title and Welcome Message
st.title("🌾 Farm Weather Assistant")

st.markdown("""
<div style="background-color:#F7FBEA; padding:15px; border-radius:10px; border: 1px solid #A3C16F;">
    <h3 style="color:#365314;">🌳 Welcome to Farm Weather Assistant</h3>
    <p style="color:#365314; font-size:16px;">
        Helping you make smarter decisions for your durian orchard every day.<br>
        Track weather, monitor GDD, predict pest risks, and optimize your farm operations with ease!
    </p>
</div>
""", unsafe_allow_html=True)

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

# 📦 Helper Functions

def load_raw_weather_file(file):
    try:
        df = pd.read_csv(file, parse_dates=['Date/Time'])
        return df
    except Exception:
        file.seek(0)
        first_bytes = file.read(10)
        file.seek(0)
        if b'<?xml' in first_bytes:
            tree = ET.parse(file)
            root = tree.getroot()
            namespace = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}

            worksheet = root.find('.//ss:Worksheet', namespace)
            table = worksheet.find('.//ss:Table', namespace)
            rows = table.findall('.//ss:Row', namespace)

            data = []
            for row in rows:
                values = []
                for cell in row.findall('.//ss:Cell', namespace):
                    data_elem = cell.find('.//ss:Data', namespace)
                    if data_elem is not None:
                        values.append(data_elem.text)
                    else:
                        values.append(None)
                data.append(values)

            header_1 = data[0]
            header_2 = data[1]
            new_columns = []
            for h1, h2 in zip(header_1, header_2):
                if pd.isna(h1) or h1 is None:
                    new_columns.append(h2)
                else:
                    new_columns.append(f"{h1} ({h2})")

            fixed_data = []
            for row in data[2:]:
                if len(row) < len(new_columns):
                    row += [None] * (len(new_columns) - len(row))
                elif len(row) > len(new_columns):
                    row = row[:len(new_columns)]
                fixed_data.append(row)

            df = pd.DataFrame(fixed_data, columns=new_columns)
            df = df.dropna(axis=1, how='all')
            df.rename(columns={df.columns[0]: 'Date/Time'}, inplace=True)
            df['Date/Time'] = pd.to_datetime(df['Date/Time'], errors='coerce')
            for col in df.columns[1:]:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            return df
        else:
            try:
                df = pd.read_excel(file, engine='xlrd')
                if 'Date/Time' not in df.columns:
                    df.columns = df.iloc[1]
                    df = df.drop([0,1]).reset_index(drop=True)
                df['Date/Time'] = pd.to_datetime(df['Date/Time'], errors='coerce')
                for col in df.columns[1:]:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                return df
            except Exception as e:
                st.error(f"❌ Could not read the file. {e}")
                return None

def calculate_gdd(df, base_temperature=10, reset_date=None):
    df = df.copy()
    if 'HC Air temperature [°C] (max)' not in df.columns or 'HC Air temperature [°C] (min)' not in df.columns:
        if 'HC Air temperature [°C] (avg)' in df.columns:
            df['GDD'] = df['HC Air temperature [°C] (avg)'] - base_temperature
        else:
            st.error("❌ Temperature data not found for GDD calculation.")
            return df
    else:
        df['GDD'] = ((df['HC Air temperature [°C] (max)'] + df['HC Air temperature [°C] (min)']) / 2) - base_temperature

    df['GDD'] = df['GDD'].apply(lambda x: x if x > 0 else 0)

    accumulated = []
    total = 0
    for idx, row in df.iterrows():
        if reset_date and row['Date/Time'].date() == reset_date:
            total = 0
        total += row['GDD']
        accumulated.append(total)

    df['Accumulated GDD'] = accumulated
    return df


# Upload file section
uploaded_file = st.file_uploader("Upload your weather station file (.csv or .xls)", type=["csv", "xls"])

if uploaded_file is not None:
    with st.spinner("Processing your file..."):
        weather_df = load_raw_weather_file(uploaded_file)
    if weather_df is not None:
        st.success("✅ Weather data loaded successfully!")
        available_columns = list(weather_df.columns)
        st.info(f"📚 **Available Data Columns:** {', '.join(available_columns)}")
else:
    weather_df = None

if weather_df is not None:
    # 🌱 Select Your Crop
    st.divider()
    st.subheader("🌱 Select Your Crop")
    selected_crop = st.selectbox("เลือกชนิดพืชที่ปลูก:", options=list(CROP_BASE_TEMPS.keys()), index=0)
    base_temp = CROP_BASE_TEMPS[selected_crop]
    st.success(f"✅ Selected Crop: {selected_crop} (Base Temperature = {base_temp}°C)")

    # 🌞 Today's Farm Weather Summary
    st.divider()
    st.subheader("🌞 Today's Farm Weather Summary")
    today = datetime.today().date()
    today_data = weather_df[weather_df['Date/Time'].dt.date == today]

    if not today_data.empty:
        rainfall_today = today_data['Precipitation [mm] (avg)'].sum() if 'Precipitation [mm] (avg)' in today_data.columns else None
        avg_temp_today = today_data['HC Air temperature [°C] (avg)'].mean() if 'HC Air temperature [°C] (avg)' in today_data.columns else None
        min_humid_today = today_data['HC Relative humidity [%] (min)'].min() if 'HC Relative humidity [%] (min)' in today_data.columns else None

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

    else:
        st.info("ℹ️ No data recorded for today.")


    # 💬 Chat with Farm Data
    st.divider()
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
            rain = weather_df['Precipitation [mm] (avg)'].sum() if 'Precipitation [mm] (avg)' in weather_df.columns else None
            if rain is not None:
                response = f"🌧️ **Total rainfall recorded: {rain:.2f} mm**."
            else:
                response = "🌧️ Rainfall data is not available."

        elif 'april' in user_lower and ('hotter' in user_lower or 'temperature' in user_lower):
            april = weather_df[weather_df['Date/Time'].dt.month == 4]
            this_year = april[april['Date/Time'].dt.year == datetime.today().year]['HC Air temperature [°C] (avg)'].mean()
            last_year = april[april['Date/Time'].dt.year == datetime.today().year - 1]['HC Air temperature [°C] (avg)'].mean()
            if pd.isna(this_year) or pd.isna(last_year):
                response = "⚠️ Not enough data for April comparison."
            else:
                response = f"🌡️ April {datetime.today().year}: {this_year:.2f} °C\n🌡️ April {datetime.today().year -1}: {last_year:.2f} °C"

        elif any(word in user_lower for word in ['advice', 'fertilize', 'recommend', 'action', 'farming']):
            response = "🌱 Based on recent weather, consider fertilizing after consistent rainfall and avoid during dry stress periods."

        elif 'pest' in user_lower or 'ศัตรูพืช' in user_lower or 'แมลง' in user_lower:
            response = "🐛 Monitor carefully! Current temperatures could favor pest activity. Increase inspection frequency."

        with st.chat_message("assistant"):
            st.markdown(response)

        st.session_state['history'].append({"role": "assistant", "content": response})

    # 📈 Weather Trends
    st.divider()
    st.subheader("📈 Weather Trends")
    time_range = st.selectbox("Select time range:", ("Last 7 Days", "Last 30 Days", "Last 90 Days", "Last 365 Days"))
    days_back = {"Last 7 Days": 7, "Last 30 Days": 30, "Last 90 Days": 90, "Last 365 Days": 365}[time_range]

    filtered_data = weather_df[weather_df['Date/Time'] > datetime.now() - timedelta(days=days_back)]

    if 'Precipitation [mm] (avg)' in filtered_data.columns:
        filtered_data['Rainfall_MA'] = filtered_data['Precipitation [mm] (avg)'].rolling(window=3).mean()
    else:
        filtered_data['Rainfall_MA'] = None

    if 'HC Air temperature [°C] (avg)' in filtered_data.columns:
        filtered_data['Temperature_MA'] = filtered_data['HC Air temperature [°C] (avg)'].rolling(window=3).mean()
    else:
        filtered_data['Temperature_MA'] = None

    if 'HC Relative humidity [%] (min)' in filtered_data.columns:
        filtered_data['Humidity_MA'] = filtered_data['HC Relative humidity [%] (min)'].rolling(window=3).mean()
    else:
        filtered_data['Humidity_MA'] = None

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 🌧️ Rainfall (Smoothed)")
        if filtered_data['Rainfall_MA'] is not None:
            rain_chart = filtered_data[['Date/Time', 'Rainfall_MA']].dropna()
            rain_chart = rain_chart.set_index('Date/Time')
            st.line_chart(rain_chart)
        else:
            st.info("No Rainfall Data Available")

    with col2:
        st.markdown("### 🌡️ Temperature (Smoothed)")
        if filtered_data['Temperature_MA'] is not None:
            temp_chart = filtered_data[['Date/Time', 'Temperature_MA']].dropna()
            temp_chart = temp_chart.set_index('Date/Time')
            st.line_chart(temp_chart)
        else:
            st.info("No Temperature Data Available")

    with col3:
        st.markdown("### 💧 Humidity (Smoothed)")
        if filtered_data['Humidity_MA'] is not None:
            humid_chart = filtered_data[['Date/Time', 'Humidity_MA']].dropna()
            humid_chart = humid_chart.set_index('Date/Time')
            st.line_chart(humid_chart)
        else:
            st.info("No Humidity Data Available")

    # 📖 Reference Values
    st.divider()
    st.subheader("📖 Reference Values and Assumptions")

    st.markdown("### 🐛 Pest Optimal Temperature Ranges")
    pest_data = []
    for pest, details in PEST_DATABASE.items():
        pest_data.append({"Pest": pest, "Topt_min (°C)": details["Topt_min"], "Topt_max (°C)": details["Topt_max"], "Notes": details["Note"]})
    pest_df = pd.DataFrame(pest_data)
    st.dataframe(pest_df)

    st.markdown("### 🌱 Crop Base Temperatures")
    crop_data = []
    for crop, base_temp in CROP_BASE_TEMPS.items():
        crop_data.append({"Crop": crop, "Base Temperature (°C)": base_temp})
    crop_df = pd.DataFrame(crop_data)
    st.dataframe(crop_df)

    st.info("""
    - GDD Target Default: **500°C-days** (modifiable later)
    - Trend smoothing: **3-day moving average**
    - Rainfall, Temperature, and Humidity trends based on station's uploaded data
    """)

# Footer
st.divider()
st.caption("🌾 Powered by Farm Weather Assistant - helping you grow smarter.")
