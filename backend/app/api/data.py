"""Data endpoints — real collected traffic data."""

from fastapi import APIRouter
import os, csv
from collections import defaultdict

router = APIRouter()

CSV_FILE = "data/real_kampala_traffic.csv"


def read_csv():
    if not os.path.exists(CSV_FILE):
        return []
    with open(CSV_FILE, encoding="utf-8") as f:
        return list(csv.DictReader(f))


@router.get("/summary")
def data_summary():
    """How many records collected so far."""
    rows = read_csv()
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
        "total_records":   len(rows),
        "unique_roads":    len(roads),
        "first_record":    rows[0].get("timestamp"),
        "last_record":     rows[-1].get("timestamp"),
        "records_per_road": dict(roads),
        "label_distribution": dict(labels),
        "data_sources": dict(sources),
    }


@router.get("/latest")
def data_latest():
    """Last 8 records (one per road)."""
    rows = read_csv()
    if not rows:
        return {"records": [], "count": 0}
    last = rows[-8:] if len(rows) >= 8 else rows
    return {"records": last, "count": len(last)}


@router.get("/all")
def data_all():
    """All collected records."""
    rows = read_csv()
    return {"records": rows, "count": len(rows)}
