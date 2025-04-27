# /modules/smart_alert.py

def classify_rainfall(rain_mm):
    if rain_mm >= 30:
        return "heavy"
    elif rain_mm >= 10:
        return "moderate"
    elif rain_mm > 0:
        return "light"
    else:
        return "no rain"

def check_pest_risk(temp_c, humidity_pct):
    if temp_c >= 28 and humidity_pct <= 60:
        return "high"
    elif temp_c >= 25:
        return "moderate"
    else:
        return "low"

def analyze_forecast(forecast_data):
    rain_risks = []
    temp_risks = []
    pest_risks = []
    
    for point in forecast_data:
        rain_mm = point.get('rain', 0)
        temp_c = point.get('temp', 0)
        humidity = point.get('humidity', 70)
        
        rain_risks.append(classify_rainfall(rain_mm))
        temp_risks.append(temp_c)
        pest_risks.append(check_pest_risk(temp_c, humidity))
    
    return {
        "rain_risk": max(rain_risks, key=rain_risks.count),
        "avg_temp": sum(temp_risks) / len(temp_risks),
        "pest_risk": max(pest_risks, key=pest_risks.count)
    }

def generate_alerts(forecast_data, gdd_value):
    analysis = analyze_forecast(forecast_data)
    alerts = []
    
    # Rain alert
    if analysis["rain_risk"] in ["heavy", "moderate"]:
        alerts.append("☔ Rain expected. Delay fertilizer or pesticide applications.")
    else:
        alerts.append("✅ Good weather for field activities.")

    # Pest alert
    if analysis["pest_risk"] == "high":
        alerts.append("🐛 High pest risk! Increase inspection and set traps.")
    elif analysis["pest_risk"] == "moderate":
        alerts.append("🐛 Moderate pest risk. Monitor closely.")

    # GDD alert
    if gdd_value and gdd_value >= 500:
        alerts.append("🌱 Crop near flowering/maturity based on GDD. Prepare harvesting plan.")
    
    return alerts
