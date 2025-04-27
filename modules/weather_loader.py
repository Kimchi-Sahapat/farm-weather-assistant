# modules/weather_loader.py

import pandas as pd
import xml.etree.ElementTree as ET

def load_weather_file(uploaded_file):
    """Load farm weather station file (CSV, Excel, XML) into a clean pandas DataFrame."""
    try:
        # Try reading as CSV first
        df = pd.read_csv(uploaded_file, parse_dates=['Date/Time'])
        return clean_weather_dataframe(df)
    
    except Exception:
        uploaded_file.seek(0)  # Reset file pointer
        first_bytes = uploaded_file.read(10)
        uploaded_file.seek(0)

        if b'<?xml' in first_bytes:
            return load_weather_from_excel_xml(uploaded_file)
        else:
            return load_weather_from_xls(uploaded_file)

def load_weather_from_excel_xml(file):
    """Load weather station Excel XML into DataFrame."""
    try:
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

        # Build DataFrame
        header_1 = data[0]
        header_2 = data[1]
        new_columns = [f"{h1} ({h2})" if h1 else h2 for h1, h2 in zip(header_1, header_2)]
        
        fixed_data = []
        for row in data[2:]:
            row += [None] * (len(new_columns) - len(row))
            fixed_data.append(row[:len(new_columns)])
        
        df = pd.DataFrame(fixed_data, columns=new_columns)
        df = clean_weather_dataframe(df)
        return df

    except Exception as e:
        print(f"⚠️ Error loading XML Excel file: {e}")
        return None

def load_weather_from_xls(file):
    """Load traditional XLS Excel weather station file into DataFrame."""
    try:
        df = pd.read_excel(file, engine='xlrd')
        if 'Date/Time' not in df.columns:
            df.columns = df.iloc[1]
            df = df.drop([0, 1]).reset_index(drop=True)
        return clean_weather_dataframe(df)
    except Exception as e:
        print(f"⚠️ Error loading XLS file: {e}")
        return None

def clean_weather_dataframe(df):
    """Clean weather DataFrame: parse dates, convert numbers."""
    df = df.dropna(axis=1, how='all')
    df.rename(columns={df.columns[0]: 'Date/Time'}, inplace=True)
    df['Date/Time'] = pd.to_datetime(df['Date/Time'], errors='coerce')
    for col in df.columns[1:]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df
