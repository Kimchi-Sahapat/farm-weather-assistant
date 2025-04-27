import pandas as pd
import xml.etree.ElementTree as ET
import streamlit as st

def load_weather_file(uploaded_file):
    try:
        # Try CSV first
        df = pd.read_csv(uploaded_file, parse_dates=["Date/Time"])
        return df
    except Exception:
        try:
            uploaded_file.seek(0)
            first_bytes = uploaded_file.read(100).decode(errors="ignore")
            uploaded_file.seek(0)

            if "<?xml" in first_bytes:
                # XML-like XLS (TMD weather file)
                root = ET.parse(uploaded_file).getroot()
                namespace = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}
                table = root.find(".//ss:Table", namespace)
                data = []
                for row in table.findall(".//ss:Row", namespace):
                    row_data = [
                        cell.find(".//ss:Data", namespace).text if cell.find(".//ss:Data", namespace) is not None else None
                        for cell in row.findall(".//ss:Cell", namespace)
                    ]
                    data.append(row_data)

                headers = [h if h else d for h, d in zip(data[0], data[1])]
                df_data = data[2:]
                df = pd.DataFrame(df_data, columns=headers)
                df.rename(columns={df.columns[0]: "Date/Time"}, inplace=True)
                df["Date/Time"] = pd.to_datetime(df["Date/Time"], errors="coerce")
                for col in df.columns[1:]:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                return df

            else:
                # Real XLS file
                uploaded_file.seek(0)
                df = pd.read_excel(uploaded_file, engine="xlrd")
                df["Date/Time"] = pd.to_datetime(df["Date/Time"], errors="coerce")
                return df

        except Exception as e:
            st.error(f"❌ Error reading file: {e}")
            return None
