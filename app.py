import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# Streamlit config
st.set_page_config(page_title="Farm Weather Assistant", page_icon="🌾", layout="wide")

# Language selection
lang = st.sidebar.radio("🌐 Language / ภาษา", ("English", "ภาษาไทย"))

# Text dictionary
TEXTS = {
    "English": {
        "upload_title": "Upload your weather station file (.csv or .xls)",
        "select_crop": "Select Your Crop",
        "weather_summary": "Today's Farm Weather Summary",
        "chat_title": "Chat with Your Farm Data",
        "trends_title": "Weather Trends",
        "powered_by": "Powered by Farm Weather Assistant - helping you grow smarter.",
        "rainfall_today": "Rainfall Today",
        "avg_temp_today": "Avg Temp Today",
        "min_humidity_today": "Min Humidity",
        "gdd_today": "GDD Today",
        "gdd_accumulated": "Accumulated GDD",
    },
    "ภาษาไทย": {
        "upload_title": "อัปโหลดไฟล์สถานีอากาศ (.csv หรือ .xls)",
        "select_crop": "เลือกชนิดพืช",
        "weather_summary": "สรุปอากาศฟาร์มวันนี้",
        "chat_title": "พูดคุยกับข้อมูลฟาร์มของคุณ",
        "trends_title": "แนวโน้มสภาพอากาศ",
        "powered_by": "ขับเคลื่อนโดย Farm Weather Assistant - เพื่อการเพาะปลูกที่ชาญฉลาด",
        "rainfall_today": "ปริมาณฝนวันนี้",
        "avg_temp_today": "อุณหภูมิเฉลี่ยวันนี้",
        "min_humidity_today": "ความชื้นต่ำสุด",
        "gdd_today": "GDD วันนี้",
        "gdd_accumulated": "GDD สะสม",
    }
}

# Databases
CROP_BASE_TEMPS = {
    "ข้าวโพด (Maize)": 10,
    "ทุเรียน (Durian)": 15,
    "มะม่วง (Mango)": 13,
    "มันสำปะหลัง (Cassava)": 8,
    "ข้าว (Rice)": 8,
    "ลิ้นจี่ (Lychee)": 7
}

# Helper functions
def load_raw_weather_file(file):
    try:
        df = pd.read_csv(file, parse_dates=["Date/Time"])
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
            df.dropna(axis=1, how="all", inplace=True)
            df.rename(columns={df.columns[0]: "Date/Time"}, inplace=True)
            df["Date/Time"] = pd.to_datetime(df["Date/Time"], errors="coerce")
            for col in df.columns[1:]:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            return df
        else:
            try:
                df = pd.read_excel(file, engine="xlrd")
                if 'Date/Time' not in df.columns:
                    df.columns = df.iloc[1]
                    df = df.drop([0, 1]).reset_index(drop=True)
                df["Date/Time"] = pd.to_datetime(df["Date/Time"], errors="coerce")
                for col in df.columns[1:]:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                return df
            except Exception as e:
                st.error(f"❌ Could not read the file: {e}")
                return None

# App main interface
st.title("🌾 Farm Weather Assistant")

uploaded_file = st.file_uploader(f"📂 {TEXTS[lang]['upload_title']}", type=["csv", "xls"])

if uploaded_file is not None:
    with st.spinner("Processing your file..."):
        weather_df = load_raw_weather_file(uploaded_file)
    if weather_df is not None:
        st.success("✅ Weather data loaded successfully!")
        st.info(f"📚 Available Columns: {', '.join(weather_df.columns)}")
    else:
        st.stop()
else:
    weather_df = None
    st.stop()

# Select Crop
st.divider()
st.subheader(f"🌱 {TEXTS[lang]['select_crop']}")
selected_crop = st.selectbox("", options=list(CROP_BASE_TEMPS.keys()))
base_temp = CROP_BASE_TEMPS[selected_crop]
st.success(f"✅ Selected: {selected_crop} (Base Temp = {base_temp}°C)")

# Weather Summary
st.divider()
st.subheader(f"🌞 {TEXTS[lang]['weather_summary']}")
today = datetime.today().date()
today_data = weather_df[weather_df['Date/Time'].dt.date == today]

if not today_data.empty:
    rainfall_today = today_data['Precipitation [mm] (avg)'].sum() if 'Precipitation [mm] (avg)' in today_data.columns else None
    avg_temp_today = today_data['HC Air temperature [°C] (avg)'].mean() if 'HC Air temperature [°C] (avg)' in today_data.columns else None
    min_humid_today = today_data['HC Relative humidity [%] (min)'].min() if 'HC Relative humidity [%] (min)' in today_data.columns else None

    if "HC Air temperature [°C] (max)" in today_data.columns and "HC Air temperature [°C] (min)" in today_data.columns:
        gdd_today = ((today_data['HC Air temperature [°C] (max)'].max() + today_data['HC Air temperature [°C] (min)'].min()) / 2) - base_temp
    elif avg_temp_today is not None:
        gdd_today = avg_temp_today - base_temp
    else:
        gdd_today = 0

    gdd_today = gdd_today if gdd_today > 0 else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(f"🌧️ {TEXTS[lang]['rainfall_today']}", f"{rainfall_today:.2f} mm" if rainfall_today else "N/A")
    with col2:
        st.metric(f"🌡️ {TEXTS[lang]['avg_temp_today']}", f"{avg_temp_today:.2f} °C" if avg_temp_today else "N/A")
    with col3:
        st.metric(f"💧 {TEXTS[lang]['min_humidity_today']}", f"{min_humid_today:.2f} %" if min_humid_today else "N/A")

else:
    st.info("ℹ️ No data recorded for today.")

# Chatbot
st.divider()
st.subheader(f"💬 {TEXTS[lang]['chat_title']}")

if "history" not in st.session_state:
    st.session_state.history = []

for message in st.session_state.history:
    align = "user" if message["role"] == "user" else "assistant"
    with st.chat_message(align):
        st.markdown(message["content"])

user_message = st.chat_input("Ask about rainfall, temperature, or farm advice!")

if user_message:
    st.session_state.history.append({"role": "user", "content": user_message})
    with st.chat_message("user"):
        st.markdown(user_message)

    response = "🤔 Sorry, I don't understand. Try asking about rain, temperature, or farming advice."
    user_lower = user_message.lower()

    if "rain" in user_lower:
        total_rain = weather_df['Precipitation [mm] (avg)'].sum() if 'Precipitation [mm] (avg)' in weather_df.columns else None
        response = f"🌧️ Total rainfall: {total_rain:.2f} mm." if total_rain else "🌧️ Rainfall data not available."
    elif "temperature" in user_lower:
        avg_temp = weather_df['HC Air temperature [°C] (avg)'].mean() if 'HC Air temperature [°C] (avg)' in weather_df.columns else None
        response = f"🌡️ Average temperature: {avg_temp:.2f} °C." if avg_temp else "🌡️ Temperature data not available."
    elif "fertilizer" in user_lower or "plant" in user_lower:
        response = "🌱 General advice: Fertilize when soil moisture is adequate and avoid during heavy rain forecasts."

    with st.chat_message("assistant"):
        st.markdown(response)

    st.session_state.history.append({"role": "assistant", "content": response})

# Footer
st.divider()
st.caption(TEXTS[lang]['powered_by'])
