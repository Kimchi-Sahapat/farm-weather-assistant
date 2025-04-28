# /modules/weather_loader.py

import pandas as pd
import xml.etree.ElementTree as ET
import io

def load_weather_file(uploaded_file):
    try:
        # Read first few bytes
        first_bytes = uploaded_file.read(20)
        uploaded_file.seek(0)

        # Check if XML
        if b'<?xml' in first_bytes or b'\xef\xbb\xbf<?xml' in first_bytes:
            # Parse XML-based XLS
            content = uploaded_file.read()
            if content.startswith(b'\xef\xbb\xbf'):
                content = content.decode('utf-8-sig').encode('utf-8')  # Remove BOM
            root = ET.fromstring(content)

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
            # Try normal CSV or XLS
            uploaded_file.seek(0)
            try:
                return pd.read_csv(uploaded_file, parse_dates=["Date/Time"])
            except:
                uploaded_file.seek(0)
                return pd.read_excel(uploaded_file, parse_dates=["Date/Time"])

    except Exception as e:
        print(f"❌ Error loading weather file: {e}")
        return None
