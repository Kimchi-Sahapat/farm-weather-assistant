import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime

# 🌍 Page Config
st.set_page_config(page_title="Farm Weather Assistant", page_icon="🌾", layout="wide")

# 🌐 Language Selector
lang = st.sidebar.radio("🌐 Language / ภาษา", ("English", "ภาษาไทย"))

# 📝 Texts
TEXTS = {
    "English": {
        "upload_title": "Upload your weather station file (.csv or .xls)",
        "select_crop": "Select Your Crop",
        "weather_summary": "Today's Farm Weather Summary",
        "reference_title": "Reference Values",
        "rainfall_today": "Rainfall Today",
        "avg_temp_today": "Avg Temp Today",
        "min_humidity_today": "Min Humidity Today",
    },
    "ภาษาไทย": {
        "upload_title": "อัปโหลดไฟล์สถานีอากาศ (.csv หรือ .xls)",
        "select_crop": "เลือกชนิดพืช",
        "weather_summary": "สรุปอากาศฟาร์มวันนี้",
        "reference_title": "ข้อมูลอ้างอิง",
        "rainfall_today": "ปริมาณฝนวันนี้",
        "avg_temp_today": "อุณหภูมิเฉลี่ยวันนี้",
        "min_humidity_today": "ความชื้นต่ำสุดวันนี้",
    }
}

# 🌱 Crop Base Temps
CROP_BASE_TEMPS = {
    "ทุเรียน (Durian)": 15,
    "ข้าวโพด (Maize)": 10,
    "มะม่วง (Mango)": 13,
    "มันสำปะหลัง (Cassava)": 8,
    "ข้าว (Rice)": 8,
    "ลิ้นจี่ (Lychee)": 7
}

# 🐛 Pest Database
PEST_DATABASE = {
    "เพลี้ยไฟ (Thrips)": {
        "Topt_min": 28,
        "Topt_max": 32,
        "advice_en": "Thrips thrive in dry, hot conditions. Inspect young shoots closely.",
        "advice_th": "เพลี้ยไฟระบาดหนักช่วงอากาศร้อนและแห้ง ตรวจสอบยอดอ่อนอย่างสม่ำเสมอ"
    },
    "เพลี้ยแป้ง (Mealybug)": {
        "Topt_min": 25,
        "Topt_max": 30,
        "advice_en": "Mealybugs prefer stable, humid conditions. Monitor closely during rainy periods.",
        "advice_th": "เพลี้ยแป้งชอบอากาศชื้น ควรตรวจสอบช่วงฤดูฝน"
    },
    "ไรแดง (Spider Mite)": {
        "Topt_min": 30,
        "Topt_max": 32,
        "advice_en": "Spider mites outbreak during hot and dry weather. Increase field scouting.",
        "advice_th": "ไรแดงระบาดในสภาพอากาศร้อนจัดและแห้ง เพิ่มความถี่ในการสำรวจแปลง"
    },
    "หนอนเจาะผลไม้ (Fruit Borer)": {
        "Topt_min": 28,
        "Topt_max": 30,
        "advice_en": "Fruit borers lay eggs on developing fruits. Bag fruits early.",
        "advice_th": "หนอนเจาะผลไม้จะวางไข่ที่ผลอ่อน ควรห่อผลตั้งแต่เนิ่นๆ"
    }
}

# 📥 Upload Weather File
st.title("🌾 Farm Weather Assistant")

uploaded_file = st.file_uploader(TEXTS[lang]["upload_title"], type=["csv", "xls"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file, parse_dates=["Date/Time"])
    except Exception:
        uploaded_file.seek(0)
        try:
            file_bytes = uploaded_file.read()
            if b"<?xml" in file_bytes[:10]:
                root = ET.fromstring(file_bytes)
                namespace = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}
                table = root.find(".//ss:Table", namespace)
                rows = table.findall(".//ss:Row", namespace)
                data = []
                for row in rows:
                    data.append([
                        cell.find(".//ss:Data", namespace).text if cell.find(".//ss:Data", namespace) is not None else None
                        for cell in row.findall(".//ss:Cell", namespace)
                    ])
                headers = [h if h else d for h, d in zip(data[0], data[1])]
                df = pd.DataFrame(data[2:], columns=headers)
                df.rename(columns={df.columns[0]: "Date/Time"}, inplace=True)
                df["Date/Time"] = pd.to_datetime(df["Date/Time"], errors="coerce")
                for col in df.columns[1:]:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            else:
                uploaded_file.seek(0)
                df = pd.read_excel(uploaded_file, engine="openpyxl")
                df["Date/Time"] = pd.to_datetime(df["Date/Time"], errors="coerce")
        except Exception as e:
            st.error(f"❌ Error loading file: {e}")
            df = None
else:
    df = None

# 🌱 If data loaded
if df is not None:
    st.success("✅ File loaded successfully!")

    # 🌾 Crop Selection
    st.subheader(f"🌱 {TEXTS[lang]['select_crop']}")
    selected_crop = st.selectbox("", list(CROP_BASE_TEMPS.keys()))
    base_temp = CROP_BASE_TEMPS[selected_crop]

    # 🌦️ Today's Weather Summary
    st.subheader(f"🌞 {TEXTS[lang]['weather_summary']}")
    today = datetime.now().date()
    today_df = df[df["Date/Time"].dt.date == today]

    if not today_df.empty:
        rainfall = today_df["Precipitation [mm] (avg)"].sum() if "Precipitation [mm] (avg)" in today_df.columns else None
        avg_temp = today_df["HC Air temperature [°C] (avg)"].mean() if "HC Air temperature [°C] (avg)" in today_df.columns else None
        min_humidity = today_df["HC Relative humidity [%] (min)"].min() if "HC Relative humidity [%] (min)" in today_df.columns else None

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(f"🌧️ {TEXTS[lang]['rainfall_today']}", f"{rainfall:.1f} mm" if rainfall else "N/A")
        with col2:
            st.metric(f"🌡️ {TEXTS[lang]['avg_temp_today']}", f"{avg_temp:.1f} °C" if avg_temp else "N/A")
        with col3:
            st.metric(f"💧 {TEXTS[lang]['min_humidity_today']}", f"{min_humidity:.1f} %" if min_humidity else "N/A")

    else:
        st.info("ℹ️ No data for today.")

# 📖 Reference Section
st.divider()
st.subheader(f"📖 {TEXTS[lang]['reference_title']}")

st.markdown("### 🌾 Crop Base Temperatures")
crop_df = pd.DataFrame([
    {"Crop": crop, "Base Temp (°C)": temp} for crop, temp in CROP_BASE_TEMPS.items()
])
st.dataframe(crop_df)

st.markdown("### 🐛 Pest Database")
pest_df = pd.DataFrame([
    {
        "Pest": pest,
        "Topt_min (°C)": data["Topt_min"],
        "Topt_max (°C)": data["Topt_max"],
        "Advice (EN)": data["advice_en"],
        "คำแนะนำ (TH)": data["advice_th"],
    }
    for pest, data in PEST_DATABASE.items()
])
st.dataframe(pest_df)

# 🌾 Footer
st.divider()
st.caption("🌾 Powered by Farm Weather Assistant")
