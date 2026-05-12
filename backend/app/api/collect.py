from fastapi import APIRouter
from app.core.database import get_conn
import datetime, requests, os

router = APIRouter()

ROADS = [
    ("kampala_rd", "Kampala Road", "-0.3168,32.5811", "-0.3152,32.5722", 10, True),
    ("jinja_rd", "Jinja Road", "-0.3047,32.6312", "-0.3152,32.5722", 25, True),
    ("entebbe_rd", "Entebbe Road", "-0.3152,32.5722", "-0.0512,32.4435", 40, False),
    ("bombo_rd", "Bombo Road", "-0.3152,32.5722", "0.5833,32.5333", 35, True),
    ("masaka_rd", "Masaka Road", "-0.3152,32.5722", "-0.3333,31.7333", 90, True),
    ("gaba_rd", "Gaba Road", "-0.3152,32.5722", "-0.3667,32.6167", 15, True),
    ("portbell_rd", "Port Bell Road", "-0.3152,32.5722", "-0.2833,32.6500", 20, True),
    ("n_bypass", "Northern Bypass", "-0.2833,32.5500", "-0.2667,32.6333", 30, False),
]

def get_weather():
    try:
        r = requests.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": 0.3136, "longitude": 32.5811,
            "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
            "timezone": "Africa/Kampala", "forecast_days": 1,
        }, timeout=10)
        d = r.json().get("current", {})
        return {"rain_mm": round(d.get("precipitation", 0.0), 2)}
    except:
        return {"rain_mm": 0.0}

def get_google_eta(origin, dest):
    try:
        r = requests.get("https://maps.googleapis.com/maps/api/directions/json", params={
            "origin": origin, "destination": dest,
            "key": os.getenv("GOOGLE_MAPS_API_KEY", "AIzaSyA1JpHbQH5symf6cssB6z-sAXRb2hkQMG4"),
            "departure_time": "now", "traffic_model": "best_guess",
        }, timeout=15)
        data = r.json()
        if data.get("status") != "OK":
            return None
        leg = data["routes"][0]["legs"][0]
        dur_n = leg["duration"]["value"]
        dur_t = leg.get("duration_in_traffic", leg["duration"])["value"]
        return round(dur_t / max(dur_n, 1), 4)
    except:
        return None

def congestion_label(ratio):
    if ratio >= 1.60: return "high"
    if ratio >= 1.25: return "medium"
    return "low"

@router.get("")
def collect():
    hour = datetime.datetime.now().hour
    weather = get_weather()
    rain = weather["rain_mm"]
    saved = 0

    try:
        conn = get_conn()
        cur = conn.cursor()
        for (road_id, road_name, origin, dest, free_flow, has_boda) in ROADS:
            ratio = get_google_eta(origin, dest)
            if ratio is None:
                rush = 1 + (0.85 if hour in (7,8,9) else 0) + (1.10 if hour in (17,18,19,20) else 0)
                ratio = round(min(3.5, max(0.5, (1 + rain * 0.025) * rush)), 4)
                source = "estimated"
            else:
                source = "google_maps"

            cur.execute("""
                INSERT INTO predictions
                (road_id, road_name, label, delay_ratio, hour, rain_mm, model_used, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (road_id, road_name, congestion_label(ratio), ratio, hour, rain, "collector", source))
            saved += 1

        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        return {"status": "error", "message": str(e)}

    return {"status": "ok", "saved": saved, "hour": hour}
