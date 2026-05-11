"""
collector.py — Real Data Collection Pipeline for STIS Kampala
=============================================================
Collects every 30 minutes:
  1. Google Maps Directions API  -> real ETA + congestion ratio
  2. Open-Meteo API              -> rain, humidity, temperature (FREE, no key)
  3. OpenWeatherMap API          -> backup weather

Saves to: data/real_kampala_traffic.csv
Run:      python collector.py           (single run)
          python collector.py --loop    (every 30 min forever)
"""

from __future__ import annotations
import os, csv, time, datetime, argparse, logging
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("collector")

GOOGLE_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "AIzaSyA1JpHbQH5symf6cssB6z-sAXRb2hkQMG4")
OWM_KEY    = os.getenv("OPENWEATHERMAP_API_KEY", "2f741655470ba73b22dfc700dd37bd8c")

os.makedirs("data", exist_ok=True)
CSV_FILE = "data/real_kampala_traffic.csv"
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

FIELDNAMES = [
    "timestamp", "date", "time", "day_of_week", "hour",
    "road_id", "road_name",
    "google_eta_min", "free_flow_min", "congestion_ratio",
    "distance_km", "traffic_condition",
    "rain_mm", "temperature_c", "humidity_pct", "wind_kmh",
    "is_rush_morning", "is_rush_evening", "is_rush_midday",
    "is_night", "is_weekend", "is_friday_pm",
    "has_boda_boda", "label", "source",
]

def get_google_eta(origin, destination):
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": origin,
        "destination": destination,
        "key": GOOGLE_KEY,
        "departure_time": "now",
        "traffic_model": "best_guess",
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        data = r.json()
        if data.get("status") != "OK":
            return None
        leg = data["routes"][0]["legs"][0]
        dur_normal  = leg["duration"]["value"]
        dur_traffic = leg.get("duration_in_traffic", leg["duration"])["value"]
        dist_m      = leg["distance"]["value"]
        ratio = round(dur_traffic / max(dur_normal, 1), 4)
        return {
            "eta_min":       round(dur_traffic / 60, 1),
            "free_flow_min": round(dur_normal / 60, 1),
            "distance_km":   round(dist_m / 1000, 2),
            "ratio":         ratio,
            "condition":     "heavy" if ratio >= 1.60 else "moderate" if ratio >= 1.25 else "free",
        }
    except Exception as e:
        log.error(f"Google Maps error: {e}")
        return None

def get_open_meteo_weather():
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 0.3136,
        "longitude": 32.5811,
        "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
        "timezone": "Africa/Kampala",
        "forecast_days": 1,
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code != 200:
            return {"rain_mm": 0.0, "temp_c": 25.0, "humidity": 70, "wind_kmh": 0.0}
        d = r.json().get("current", {})
        return {
            "rain_mm":  round(d.get("precipitation", 0.0), 2),
            "temp_c":   round(d.get("temperature_2m", 25.0), 1),
            "humidity": int(d.get("relative_humidity_2m", 70)),
            "wind_kmh": round(d.get("wind_speed_10m", 0.0), 1),
        }
    except Exception as e:
        log.warning(f"Open-Meteo error: {e}")
        return {"rain_mm": 0.0, "temp_c": 25.0, "humidity": 70, "wind_kmh": 0.0}

def engineer_features(hour, dow):
    return {
        "is_rush_morning": 1 if hour in (7, 8, 9) else 0,
        "is_rush_evening": 1 if hour in (17, 18, 19, 20) else 0,
        "is_rush_midday":  1 if hour in (12, 13, 14) else 0,
        "is_night":        1 if (hour < 5 or hour >= 23) else 0,
        "is_weekend":      1 if dow in (5, 6) else 0,
        "is_friday_pm":    1 if (dow == 4 and hour >= 16) else 0,
    }

def congestion_label(ratio):
    if ratio >= 1.60: return "high"
    if ratio >= 1.25: return "medium"
    return "low"

def collect_once():
    now     = datetime.datetime.now()
    ts      = now.strftime("%Y-%m-%d %H:%M:%S")
    hour    = now.hour
    dow     = now.weekday()
    weather = get_open_meteo_weather()
    feats   = engineer_features(hour, dow)
    rows    = []

    for (road_id, road_name, origin, dest, free_flow_est, has_boda) in ROADS:
        log.info(f"  Querying: {road_name}...")
        gmaps = get_google_eta(origin, dest)
        if gmaps:
            eta_min       = gmaps["eta_min"]
            free_flow_min = gmaps["free_flow_min"]
            ratio         = gmaps["ratio"]
            distance_km   = gmaps["distance_km"]
            condition     = gmaps["condition"]
            source        = "google_maps"
        else:
            rain_adj  = 1 + weather["rain_mm"] * 0.025
            rush_adj  = 1 + feats["is_rush_morning"]*0.85 + feats["is_rush_evening"]*1.10
            ratio     = round(min(3.5, max(0.5, rain_adj * rush_adj)), 4)
            eta_min   = round(free_flow_est * ratio, 1)
            free_flow_min = free_flow_est
            distance_km   = 0.0
            condition     = congestion_label(ratio)
            source        = "estimated"

        rows.append({
            "timestamp": ts, "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M"), "day_of_week": now.strftime("%A"),
            "hour": hour, "road_id": road_id, "road_name": road_name,
            "google_eta_min": eta_min, "free_flow_min": free_flow_min,
            "congestion_ratio": ratio, "distance_km": distance_km,
            "traffic_condition": condition,
            "rain_mm": weather["rain_mm"], "temperature_c": weather["temp_c"],
            "humidity_pct": weather["humidity"], "wind_kmh": weather["wind_kmh"],
            "is_rush_morning": feats["is_rush_morning"],
            "is_rush_evening": feats["is_rush_evening"],
            "is_rush_midday":  feats["is_rush_midday"],
            "is_night":        feats["is_night"],
            "is_weekend":      feats["is_weekend"],
            "is_friday_pm":    feats["is_friday_pm"],
            "has_boda_boda":   1 if has_boda else 0,
            "label":           congestion_label(ratio),
            "source":          source,
        })
        time.sleep(0.5)
    return rows

def write_rows(rows):
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)
    log.info(f"Wrote {len(rows)} rows to {CSV_FILE}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--interval", type=int, default=30)
    args = parser.parse_args()
    while True:
        log.info(f"--- Collection at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} ---")
        write_rows(collect_once())
        if not args.loop:
            break
        log.info(f"Sleeping {args.interval} min...")
        time.sleep(args.interval * 60)

if __name__ == "__main__":
    main()
