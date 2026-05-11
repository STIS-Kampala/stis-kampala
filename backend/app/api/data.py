"""Data endpoints — real collected traffic data."""

from fastapi import APIRouter
from collections import defaultdict
from app.core.database import get_conn

router = APIRouter()


def read_db():
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT road_id, road_name, label, delay_ratio,
                   hour, rain_mm, model_used, timestamp, source
            FROM predictions ORDER BY timestamp
        """)
        cols = ["road_id", "road_name", "label", "delay_ratio",
                "hour", "rain_mm", "model_used", "timestamp", "source"]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        print(f"DB read error: {e}")
        return []


@router.get("/summary")
def data_summary():
    rows = read_db()
    if not rows:
        return {"total_records": 0, "message": "No data collected yet"}

    roads = defaultdict(int)
    labels = defaultdict(int)
    sources = defaultdict(int)

    for r in rows:
        roads[r.get("road_name", "unknown")] += 1
        labels[r.get("label", "unknown")] += 1
        sources[r.get("source", "unknown")] += 1

    return {
        "total_records":      len(rows),
        "unique_roads":       len(roads),
        "first_record":       str(rows[0].get("timestamp")),
        "last_record":        str(rows[-1].get("timestamp")),
        "records_per_road":   dict(roads),
        "label_distribution": dict(labels),
        "data_sources":       dict(sources),
    }


@router.get("/latest")
def data_latest():
    rows = read_db()
    if not rows:
        return {"records": [], "count": 0}
    last = rows[-8:] if len(rows) >= 8 else rows
    return {"records": last, "count": len(last)}


@router.get("/all")
def data_all():
    rows = read_db()
    return {"records": rows, "count": len(rows)}
