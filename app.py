# app_pretty.py (final final patch: smart file detection)
# Streamlit Web App: Farm Weather Assistant (Beautiful UI + Full Smart Format Support)

import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="Farm Weather Assistant", page_icon="🌾", layout="wide")

# Default file path
DATA_FILE = 'Cleaned_Farm_Weather_Data.csv'

@st.cache_data

def load_raw_weather_file(file):
    try:
        # Try reading as CSV first
        df = pd.read_csv(file, parse_dates=['Date/Time'])
        return df
    except Exception:
        file.seek(0)  # Rewind file pointer
        first_bytes = file.read(10)
        file.seek(0)
        if b'<?xml' in first_bytes:
            # XML format detected
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

            df = pd.DataFrame(data[2:], columns=new_columns)
            df = df.dropna(axis=1, how='all')
            df.rename(columns={df.columns[0]: 'Date/Time'}, inplace=True)
            df['Date/Time'] = pd.to_datetime(df['Date/Time'], errors='coerce')
            for col in df.columns[1:]:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            return df
        else:
            try:
                # Otherwise try binary Excel reading
                df = pd.read_excel(file, engine='xlrd')
                if 'Date/Time' not in df.columns:
                    df.columns = df.iloc[1]
                    df = df.drop([0,1]).reset_index(drop=True)
                df['Date/Time'] = pd.to_datetime(df['Date/Time'], errors='coerce')
                for col in df.columns[1:]:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                return df
            except Exception as e:
                st.error(f"❌ Could not read the file. Please upload a valid Cleaned CSV, Station XML, or Station XLS file.\n(Technical error: {e})")
                return None

# Helper functions (same as before)
# ... (remaining part of the app stays the same)
