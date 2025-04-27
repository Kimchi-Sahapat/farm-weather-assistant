# 📖 Reference Values - Pest Info, Crop GDD Info

import streamlit as st
import pandas as pd

# 🗺️ Language and Text Dictionary from app
lang = st.session_state.get('lang', 'English')
TEXTS = st.session_state.get('TEXTS', {})

# 📚 Reference Page
st.title("📖 " + TEXTS[lang]["reference_title"])

# 📋 Pest Temperature Optimal Ranges
st.subheader("🐛 Pest Optimal Temperature Ranges")

PEST_DATABASE = {
    "เพลี้ยไฟ": {"Topt_min": 28, "Topt_max": 32, "Note_EN": "Sensitive to light and dry air.", "Note_TH": "ไวต่อแสงและอากาศแห้ง"},
    "เพลี้ยแป้ง": {"Topt_min": 25, "Topt_max": 30, "Note_EN": "Prefers stable climates.", "Note_TH": "ชอบภูมิอากาศคงที่"},
    "ไรแดง": {"Topt_min": 30, "Topt_max": 32, "Note_EN": "Outbreaks in dry air.", "Note_TH": "ระบาดในอากาศแห้ง"},
    "หนอนเจาะผลไม้": {"Topt_min": 28, "Topt_max": 30, "Note_EN": "Damages mango, durian fruits.", "Note_TH": "ทำลายมะม่วง ทุเรียน"},
    "ด้วงวงมะม่วง": {"Topt_min": 30, "Topt_max": 30, "Note_EN": "Active during hot seasons.", "Note_TH": "เคลื่อนไหวมากฤดูร้อน"},
    "หนอนกระทู้": {"Topt_min": 27, "Topt_max": 30, "Note_EN": "Life cycle accelerates in heat.", "Note_TH": "วงจรชีวิตเร็วขึ้นในอากาศร้อน"},
    "แมลงวันผลไม้": {"Topt_min": 27, "Topt_max": 30, "Note_EN": "Lays eggs during ripening.", "Note_TH": "วางไข่ช่วงผลไม้สุก"}
}

pest_data = []
for pest, info in PEST_DATABASE.items():
    pest_data.append({
        "Pest": pest,
        "Topt Min (°C)": info['Topt_min'],
        "Topt Max (°C)": info['Topt_max'],
        "Note": info['Note_TH'] if lang == "ภาษาไทย" else info['Note_EN']
    })

pest_df = pd.DataFrame(pest_data)
st.dataframe(pest_df, use_container_width=True)

# 🌱 Crop Base Temperatures for GDD
st.subheader("🌱 Crop Base Temperatures (for GDD Calculation)")

CROP_BASE_TEMPS = {
    "ทุเรียน (Durian)": 15,
    "ข้าวโพด (Maize)": 10,
    "มะม่วง (Mango)": 13,
    "มันสำปะหลัง (Cassava)": 8,
    "ข้าว (Rice)": 8,
    "ลิ้นจี่ (Lychee)": 7
}

crop_data = []
for crop, temp in CROP_BASE_TEMPS.items():
    crop_data.append({
        "Crop": crop,
        "Base Temp (°C)": temp
    })

crop_df = pd.DataFrame(crop_data)
st.dataframe(crop_df, use_container_width=True)

# ℹ️ Notes
st.info("""
- 🌾 **GDD Target Default**: 500°C-days
- 🌧️ **Weather Trends**: 3-day moving average smoothing
- 🐛 **Pest Monitoring**: Risk increases above optimal temperature zones
""")
