# app.py
# Streamlit Web App: Farm Weather Assistant (Enhanced with Upload Feature)

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# Default file path
DATA_FILE = 'Cleaned_Farm_Weather_Data.csv'

@st.cache_data
def load_data(file):
    return pd.read_csv(file, parse_dates=['Date/Time'])

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

# Streamlit App UI
st.title("🌾 Farm Weather Assistant")
st.markdown("Analyze your farm's weather patterns and receive actionable advice.")
st.divider()

# File uploader
uploaded_file = st.file_uploader("Upload a Cleaned Farm Weather CSV", type=["csv"])

if uploaded_file is not None:
    weather_df = load_data(uploaded_file)
    st.success("✅ Weather data loaded successfully!")
elif os.path.exists(DATA_FILE):
    weather_df = load_data(DATA_FILE)
    st.info("ℹ️ Using default Cleaned_Farm_Weather_Data.csv.")
else:
    weather_df = None
    st.error("❌ No weather data available.")

st.divider()

if weather_df is not None:
    query = st.text_input("Ask a question (e.g., 'rainfall last month', 'compare April', 'farming advice'):")

    if st.button("Get Answer"):
        if 'rain' in query.lower() and 'last month' in query.lower():
            rain = get_total_rainfall_last_month(weather_df)
            st.success(f"🌧️ Total Rainfall Last Month: **{rain:.2f} mm**")

        elif 'april' in query.lower() and ('hotter' in query.lower() or 'temperature' in query.lower()):
            this_year, last_year = compare_april_temperature(weather_df)
            if pd.isna(this_year) or pd.isna(last_year):
                st.warning("⚠️ Not enough data available for temperature comparison.")
            else:
                st.info(f"🌡️ **April {datetime.today().year}** Avg Temp: **{this_year:.2f} °C**\n\n🌡️ **April {datetime.today().year-1}** Avg Temp: **{last_year:.2f} °C**")

        elif any(word in query.lower() for word in ['advice', 'farming', 'recommend', 'action']):
            recommendation = recommend_agriculture_action(weather_df)
            st.success(recommendation)

        else:
            st.warning("⚠️ Sorry, I didn't recognize the question. Try asking about rainfall, April temperature, or farming actions.")
