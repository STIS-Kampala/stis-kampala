"""Weather endpoint — real Kampala weather from Open-Meteo + OpenWeatherMap."""

from fastapi import APIRouter
import requests
import os

router = APIRouter()

OWM_KEY = os.getenv("OPENWEATHERMAP_API_KEY", "2f741655470ba73b22dfc700dd37bd8c")


def get_weather():
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude":    0.3136,
            "longitude":   32.5811,
            "current":     "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
            "timezone":    "Africa/Kampala",
            "forecast_days": 1,
        }
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            d = r.json().get("current", {})
            return {
                "rain_mm":     round(d.get("precipitation", 0.0), 2),
                "temp_c":      round(d.get("temperature_2m", 25.0), 1),
                "humidity":    int(d.get("relative_humidity_2m", 70)),
                "wind_kmh":    round(d.get("wind_speed_10m", 0.0), 1),
                "is_raining":  d.get("precipitation", 0.0) > 0,
                "source":      "open-meteo",
            }
    except Exception:
        pass
    return {
        "rain_mm": 0.0, "temp_c": 25.0,
        "humidity": 70, "wind_kmh": 0.0,
        "is_raining": False, "source": "unavailable",
    }


@router.get("/current")
def current_weather():
    """Real-time Kampala weather."""
    return {"city": "Kampala", **get_weather()}


@router.get("/forecast")
def weather_forecast():
    """5-day forecast for Kampala."""
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude":    0.3136,
            "longitude":   32.5811,
            "hourly":      "temperature_2m,precipitation,relative_humidity_2m",
            "timezone":    "Africa/Kampala",
            "forecast_days": 5,
        }
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            d = r.json().get("hourly", {})
            times  = d.get("time", [])
            temps  = d.get("temperature_2m", [])
            rains  = d.get("precipitation", [])
            humid  = d.get("relative_humidity_2m", [])
            items  = [
                {"dt_txt": t, "temp_c": temp, "rain_mm": rain, "humidity": h}
                for t, temp, rain, h in zip(times, temps, rains, humid)
            ]
            return {"forecast": items, "count": len(items)}
    except Exception:
        pass
    return {"forecast": [], "count": 0}
