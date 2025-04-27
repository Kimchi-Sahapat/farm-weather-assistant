# app.py
# Streamlit Web App: Farm Weather Assistant (Chatbot Version + Pest Warning + Raw XLS Support)

import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import os

# Default file path
DATA_FILE = 'Cleaned_Farm_Weather_Data.csv'

@st.cache_data

def load_raw_weather_file(file):
    try:
        # Try reading as CSV first
        df = pd.read_csv(file, parse_dates=['Date/Time'])
        return df
    except Exception:
        # Try parsing as XML Spreadsheet 2003 (special .xls)
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

        # Handle header
        header_1 = data[0]
        header_2 = data[1]
        new_columns = []
        for h1, h2 in zip(header_1, header_2):
            if pd.isna(h1) or h1 is None:
                new_columns.append(h2)
            else:
                new_columns.append(f"{h1} ({h2})")

        df = pd.DataFrame(data[2:], columns=new_columns)

        # Drop fully empty columns
        df = df.dropna(axis=1, how='all')

        # Fix Date/Time
        df.rename(columns={df.columns[0]: 'Date/Time'}, inplace=True)
        df['Date/Time'] = pd.to_datetime(df['Date/Time'], errors='coerce')

        # Convert numerical columns
        for col in df.columns[1:]:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        return df

# Helper functions
def get_total_rainfall_last_month(df):
    today = datetime.today()
    first_day_last_month = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
    last_day_last_month = today.replace(day=1) - timedelta(days=1)
    mask = (df['Date/Time'] >= first_day_last_month) & (df['Date/Time'] <= last_day_last_month)
    total_rain = df.loc[mask, 'Precipitation [mm] (avg)'].sum()
    return total_rain

def compare_april_temperature(df):
    current_year = datetime.today().year
    april_this_year = df[(df['Date/Time'].dt.month == 4) & (df['Date/Time'].dt.year == current_year)]
    april_last_year = df[(df['Date/Time'].dt.month == 4) & (df['Date/Time'].dt.year == current_year - 1)]
    avg_this_year = april_this_year['HC Air temperature [°C] (avg)'].mean()
    avg_last_year = april_last_year['HC Air temperature [°C] (avg)'].mean()
    return avg_this_year, avg_last_year

def recommend_agriculture_action(df):
    recent_days = df[df['Date/Time'] > datetime.now() - timedelta(days=7)]
    avg_rain = recent_days['Precipitation [mm] (avg)'].mean()
    avg_humidity = recent_days['HC Relative humidity [%] (min)'].mean()
    if avg_rain > 50 and avg_humidity > 80:
        return "🔧 High rain and humidity detected. ⚠️ Be cautious of fungal diseases."
    elif avg_rain > 30:
        return "💚 Recent rains suggest it's a good time for fertilization."
    else:
        return "📍 No special agricultural actions recommended at this time."

# Pest thresholds database
PEST_DATABASE = {
    "เพลี้ยไฟ": {"Topt_min": 28, "Topt_max": 32, "Note": "Sensitive to light and low humidity."},
    "เพลี้ยแป้ง": {"Topt_min": 25, "Topt_max": 30, "Note": "Prefers stable climates."},
    "ไรแดง": {"Topt_min": 30, "Topt_max": 32, "Note": "Outbreaks in dry air."},
    "หนอนเจาะผลไม้": {"Topt_min": 28, "Topt_max": 30, "Note": "Very important in mango/durian."},
    "ด้วงวงมะม่วง": {"Topt_min": 30, "Topt_max": 30, "Note": "Moves quickly during hot season."},
    "หนอนกระทู้": {"Topt_min": 27, "Topt_max": 30, "Note": "Life cycle speed up."},
    "แมลงวันผลไม้": {"Topt_min": 27, "Topt_max": 30, "Note": "Lays eggs during early ripening."}
}

def check_pest_risks(df):
    recent_days = df[df['Date/Time'] > datetime.now() - timedelta(days=7)]
    avg_temp = recent_days['HC Air temperature [°C] (avg)'].mean()
    pest_warnings = []

    for pest, data in PEST_DATABASE.items():
        if data['Topt_min'] <= avg_temp <= data['Topt_max']:
            pest_warnings.append(f"- **{pest}**: Avg Temp {avg_temp:.1f}°C matches Topt {data['Topt_min']}-{data['Topt_max']}°C → {data['Note']}")

    if pest_warnings:
        return "⚠️ **Pest Risk Detected:**\n" + "\n".join(pest_warnings)
    else:
        return "✅ No significant pest risks detected based on recent temperatures."

# Streamlit App UI
st.title("🌾 Farm Weather Assistant - Chat Mode")
st.markdown("Chat naturally with your farm weather data!")
st.divider()

# File uploader
uploaded_file = st.file_uploader("Upload a Cleaned CSV or Raw XLS from Weather Station", type=["csv", "xls"])

if uploaded_file is not None:
    weather_df = load_raw_weather_file(uploaded_file)
    st.success("✅ Weather data loaded successfully!")
elif os.path.exists(DATA_FILE):
    weather_df = load_raw_weather_file(DATA_FILE)
    st.info("ℹ️ Using default Cleaned_Farm_Weather_Data.csv.")
else:
    weather_df = None
    st.error("❌ No weather data available.")

st.divider()

if weather_df is not None:
    if 'history' not in st.session_state:
        st.session_state['history'] = []

    for message in st.session_state['history']:
        with st.chat_message(message['role']):
            st.markdown(message['content'])

    user_message = st.chat_input("Ask about rainfall, temperature, farming advice, or pest risks!")

    if user_message:
        st.session_state['history'].append({"role": "user", "content": user_message})

        with st.chat_message("user"):
            st.markdown(user_message)

        response = "🤔 Sorry, I didn't understand. Try asking about rainfall, April temperature, farming advice, or pest risks."

        user_lower = user_message.lower()

        if 'rain' in user_lower and ('last month' in user_lower or 'rainfall' in user_lower):
            rain = get_total_rainfall_last_month(weather_df)
            response = f"🌧️ Total rainfall last month: **{rain:.2f} mm**."

        elif 'april' in user_lower and ('hotter' in user_lower or 'temperature' in user_lower):
            this_year, last_year = compare_april_temperature(weather_df)
            if pd.isna(this_year) or pd.isna(last_year):
                response = "⚠️ Not enough data available for April temperature comparison."
            else:
                response = f"🌡️ April {datetime.today().year}: **{this_year:.2f} °C**\n🌡️ April {datetime.today().year-1}: **{last_year:.2f} °C**."

        elif any(word in user_lower for word in ['advice', 'fertilize', 'recommend', 'action', 'farming']):
            recommendation = recommend_agriculture_action(weather_df)
            response = recommendation

        elif 'pest' in user_lower or 'ศัตรูพืช' in user_lower or 'แมลง' in user_lower:
            response = check_pest_risks(weather_df)

        with st.chat_message("assistant"):
            st.markdown(response)

        st.session_state['history'].append({"role": "assistant", "content": response})
