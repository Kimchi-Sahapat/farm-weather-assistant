import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import os

# Streamlit page config
st.set_page_config(page_title="Farm Weather Assistant", page_icon="🌾", layout="wide")

# Title and Welcome
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

# Sidebar
with st.sidebar:
    st.markdown("### 🌾 Farm Weather Assistant")
    st.markdown("Helping you grow smarter 📈🌱")
    st.divider()
    with st.expander("📂 Navigation Menu", expanded=True):
        page = st.radio("", ["📊 Dashboard", "📖 Reference Values"], index=0)
    st.divider()
    st.caption("Powered by Farm Weather Assistant 🌾")

# Databases
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
    "ข้าวโพด (Maize)": 10, "ทุเรียน (Durian)": 15, "มะม่วง (Mango)": 13,
    "มันสำปะหลัง (Cassava)": 8, "ข้าว (Rice)": 8, "ลิ้นจี่ (Lychee)": 7
}

# Helper Functions
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
                    values.append(data_elem.text if data_elem is not None else None)
                data.append(values)
            header_1 = data[0]
            header_2 = data[1]
            new_columns = [f"{h1} ({h2})" if h1 else h2 for h1, h2 in zip(header_1, header_2)]
            fixed_data = []
            for row in data[2:]:
                row += [None] * (len(new_columns) - len(row))
                fixed_data.append(row[:len(new_columns)])
            df = pd.DataFrame(fixed_data, columns=new_columns)
            df.dropna(axis=1, how='all', inplace=True)
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
                    df = df.drop([0, 1]).reset_index(drop=True)
                df['Date/Time'] = pd.to_datetime(df['Date/Time'], errors='coerce')
                for col in df.columns[1:]:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                return df
            except Exception as e:
                st.error(f"❌ Could not read the file: {e}")
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

# 🔥 Start Page Rendering based on Sidebar Selection
if page == "📊 Dashboard":
    uploaded_file = st.file_uploader("📂 Upload your weather station file (.csv or .xls)", type=["csv", "xls"])
    
    if uploaded_file is not None:
        with st.spinner("Processing your file..."):
            weather_df = load_raw_weather_file(uploaded_file)
        if weather_df is not None:
            st.success("✅ Weather data loaded successfully!")
            available_columns = list(weather_df.columns)
            st.info(f"📚 **Available Columns:** {', '.join(available_columns)}")
    else:
        weather_df = None

    if weather_df is not None:
        # 🌱 Select Your Crop
        st.divider()
        st.subheader("🌱 Select Crop")
        selected_crop = st.selectbox("Choose your crop:", options=list(CROP_BASE_TEMPS.keys()))
        base_temp = CROP_BASE_TEMPS[selected_crop]
        st.success(f"✅ Selected: {selected_crop} (Base Temp = {base_temp}°C)")

        # 🌞 Today's Weather Summary
        st.divider()
        st.subheader("🌞 Today's Farm Weather Summary")
        today = datetime.today().date()
        today_data = weather_df[weather_df['Date/Time'].dt.date == today]

        if not today_data.empty:
            rainfall_today = today_data['Precipitation [mm] (avg)'].sum() if 'Precipitation [mm] (avg)' in today_data.columns else None
            avg_temp_today = today_data['HC Air temperature [°C] (avg)'].mean() if 'HC Air temperature [°C] (avg)' in today_data.columns else None
            min_humid_today = today_data['HC Relative humidity [%] (min)'].min() if 'HC Relative humidity [%] (min)' in today_data.columns else None

            if 'HC Air temperature [°C] (max)' in today_data.columns and 'HC Air temperature [°C] (min)' in today_data.columns:
                gdd_today = ((today_data['HC Air temperature [°C] (max)'].max() + today_data['HC Air temperature [°C] (min)'].min()) / 2) - base_temp
            elif avg_temp_today is not None:
                gdd_today = avg_temp_today - base_temp
            else:
                gdd_today = None

            gdd_today = gdd_today if gdd_today and gdd_today > 0 else 0
            reset_start_date = datetime(2024, 12, 1).date()
            gdd_df = calculate_gdd(weather_df, base_temperature=base_temp, reset_date=reset_start_date)
            last_gdd = gdd_df['Accumulated GDD'].iloc[-1] if 'Accumulated GDD' in gdd_df.columns else None

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🌧️ Rainfall Today", f"{rainfall_today:.2f} mm" if rainfall_today else "Data Not Found")
            with col2:
                st.metric("🌡️ Avg Temp Today", f"{avg_temp_today:.2f} °C" if avg_temp_today else "Data Not Found")
            with col3:
                st.metric("💧 Min Humidity", f"{min_humid_today:.2f} %" if min_humid_today else "Data Not Found")

            col4, col5 = st.columns(2)
            with col4:
                st.metric("🌱 GDD Today", f"{gdd_today:.2f} °C-days" if gdd_today else "Data Not Found")
            with col5:
                st.metric("🌱 Accumulated GDD", f"{last_gdd:.2f} °C-days" if last_gdd else "Data Not Found")
        else:
            st.info("ℹ️ No data recorded for today.")

        # 💬 Chatbot Section
        st.divider()
        st.subheader("💬 Chat with Your Farm Data")

        if 'history' not in st.session_state:
            st.session_state['history'] = []

        for message in st.session_state['history']:
            align = "user" if message['role'] == "user" else "assistant"
            with st.chat_message(align):
                st.markdown(message['content'])

        user_message = st.chat_input("Ask about rainfall, temperature, advice, pests!")

        if user_message:
            st.session_state['history'].append({"role": "user", "content": user_message})
            with st.chat_message("user"):
                st.markdown(user_message)

            response = "🤔 Sorry, I didn't understand. Try asking about rainfall, temperature, advice, or pests."
            user_lower = user_message.lower()

            if 'rain' in user_lower and ('last month' in user_lower or 'rainfall' in user_lower):
                rain = weather_df['Precipitation [mm] (avg)'].sum() if 'Precipitation [mm] (avg)' in weather_df.columns else None
                if rain is not None:
                    response = f"🌧️ Total rainfall: **{rain:.2f} mm**."
            elif 'april' in user_lower and ('hotter' in user_lower or 'temperature' in user_lower):
                april = weather_df[weather_df['Date/Time'].dt.month == 4]
                this_year = april[april['Date/Time'].dt.year == datetime.today().year]['HC Air temperature [°C] (avg)'].mean()
                last_year = april[april['Date/Time'].dt.year == datetime.today().year - 1]['HC Air temperature [°C] (avg)'].mean()
                if pd.isna(this_year) or pd.isna(last_year):
                    response = "⚠️ Not enough data for April comparison."
                else:
                    response = f"🌡️ April {datetime.today().year}: {this_year:.2f} °C vs {datetime.today().year -1}: {last_year:.2f} °C."
            elif any(word in user_lower for word in ['advice', 'fertilize', 'recommend', 'farming']):
                response = "🌱 Recommendation: Fertilize after 2–3 days of consistent rain, avoid during dry heat."
            elif 'pest' in user_lower or 'ศัตรูพืช' in user_lower or 'แมลง' in user_lower:
                response = "🐛 Pest Alert: Current temperatures favor pest outbreaks! Inspect frequently."

            with st.chat_message("assistant"):
                st.markdown(response)

            st.session_state['history'].append({"role": "assistant", "content": response})

        # 📈 Weather Trends Section
        st.divider()
        st.subheader("📈 Weather Trends")

        time_range = st.selectbox("Select Time Range:", ("Last 7 Days", "Last 30 Days", "Last 90 Days", "Last 365 Days"))
        days_back = {"Last 7 Days": 7, "Last 30 Days": 30, "Last 90 Days": 90, "Last 365 Days": 365}[time_range]

        if 'Date/Time' in weather_df.columns:
            filtered_data = weather_df[weather_df['Date/Time'] > datetime.now() - timedelta(days=days_back)]

            if 'Precipitation [mm] (avg)' in filtered_data.columns:
                filtered_data['Rainfall_MA'] = filtered_data['Precipitation [mm] (avg)'].rolling(window=3).mean()
            if 'HC Air temperature [°C] (avg)' in filtered_data.columns:
                filtered_data['Temperature_MA'] = filtered_data['HC Air temperature [°C] (avg)'].rolling(window=3).mean()
            if 'HC Relative humidity [%] (min)' in filtered_data.columns:
                filtered_data['Humidity_MA'] = filtered_data['HC Relative humidity [%] (min)'].rolling(window=3).mean()

            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("### 🌧️ Rainfall (Smoothed)")
                st.line_chart(filtered_data[['Date/Time', 'Rainfall_MA']].dropna().set_index('Date/Time'))

            with col2:
                st.markdown("### 🌡️ Temperature (Smoothed)")
                st.line_chart(filtered_data[['Date/Time', 'Temperature_MA']].dropna().set_index('Date/Time'))

            with col3:
                st.markdown("### 💧 Humidity (Smoothed)")
                st.line_chart(filtered_data[['Date/Time', 'Humidity_MA']].dropna().set_index('Date/Time'))

        else:
            st.error("⚠️ 'Date/Time' column missing in uploaded data.")

elif page == "📖 Reference Values":
    st.subheader("📖 Reference Values and Assumptions")

    st.markdown("### 🐛 Pest Optimal Temperature Ranges")
    pest_data = [{"Pest": k, "Topt_min (°C)": v["Topt_min"], "Topt_max (°C)": v["Topt_max"], "Note": v["Note"]} for k, v in PEST_DATABASE.items()]
    st.dataframe(pd.DataFrame(pest_data))

    st.markdown("### 🌱 Crop Base Temperatures")
    crop_data = [{"Crop": k, "Base Temp (°C)": v} for k, v in CROP_BASE_TEMPS.items()]
    st.dataframe(pd.DataFrame(crop_data))

    st.info("""
    - 🌾 GDD Target: 500°C-days (adjustable later)
    - 🌦️ 3-day moving average smoothing
    - 📈 Trend charts based on uploaded data
    """)

# Footer
st.divider()
st.caption("🌾 Powered by Farm Weather Assistant - helping you grow smarter.")
