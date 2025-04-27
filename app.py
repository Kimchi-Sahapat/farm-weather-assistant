# app.py
# Streamlit Web App: Farm Weather Assistant (Chatbot Version)

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
st.title("🌾 Farm Weather Assistant - Chat Mode")
st.markdown("Chat naturally with your farm weather data!")
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
    # Chat Interface
    if 'history' not in st.session_state:
        st.session_state['history'] = []

    for message in st.session_state['history']:
        with st.chat_message(message['role']):
            st.markdown(message['content'])

    user_message = st.chat_input("Ask about rainfall, temperature, or farming advice!")

    if user_message:
        st.session_state['history'].append({"role": "user", "content": user_message})
        
        with st.chat_message("user"):
            st.markdown(user_message)

        # Bot thinking
        response = "🤔 Sorry, I didn't understand. Try asking about rainfall, April temperature, or farming advice."

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

        with st.chat_message("assistant"):
            st.markdown(response)

        st.session_state['history'].append({"role": "assistant", "content": response})
