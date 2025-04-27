# /modules/task_planner.py

def is_suitable_for_fertilization(rain_risk):
    return rain_risk in ["no rain", "light"]

def is_harvest_approaching(gdd_value):
    return gdd_value and gdd_value >= 500

def suggest_tasks(forecast_data, gdd_value):
    tasks = []

    rain_risks = []
    for point in forecast_data:
        rain_mm = point.get('rain', 0)
        if rain_mm >= 30:
            rain_risks.append("heavy")
        elif rain_mm >= 10:
            rain_risks.append("moderate")
        elif rain_mm > 0:
            rain_risks.append("light")
        else:
            rain_risks.append("no rain")

    most_common_rain = max(rain_risks, key=rain_risks.count)

    # Fertilization task
    if is_suitable_for_fertilization(most_common_rain):
        tasks.append("🌱 Good week for fertilizing or pesticide application.")
    else:
        tasks.append("⚠️ High rain risk. Postpone fertilizer application.")

    # Pest monitoring
    temp_avg = sum([p.get('temp', 0) for p in forecast_data]) / len(forecast_data)
    humidity_avg = sum([p.get('humidity', 70) for p in forecast_data]) / len(forecast_data)

    if temp_avg >= 28 and humidity_avg <= 60:
        tasks.append("🐛 Increase pest monitoring (high outbreak risk).")
    else:
        tasks.append("✅ Normal pest monitoring recommended.")

    # Harvesting preparation
    if is_harvest_approaching(gdd_value):
        tasks.append("🌾 Prepare harvesting plans. GDD approaching maturity.")
    
    return tasks
