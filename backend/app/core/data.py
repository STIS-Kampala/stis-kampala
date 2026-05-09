from dataclasses import dataclass
from typing import Dict

@dataclass(frozen=True)
class RoadConfig:
    id:       str
    name:     str
    type:     str
    base_min: int
    km:       float
    has_boda: bool
    label:    str

ROADS: Dict[str, RoadConfig] = {
    r.id: r for r in [
        RoadConfig("kampala_rd",  "Kampala Road",  "urban",   10, 3.0,  True,  "high"  ),
        RoadConfig("jinja_rd",    "Jinja Road",    "highway", 25, 8.0,  True,  "high"  ),
        RoadConfig("bombo_rd",    "Bombo Road",    "highway", 28, 28.0, True,  "medium"),
        RoadConfig("masaka_rd",   "Masaka Road",   "highway", 35, 35.0, True,  "medium"),
        RoadConfig("gaba_rd",     "Gaba Road",     "urban",   15, 7.0,  True,  "medium"),
        RoadConfig("portbell_rd", "Port Bell Rd",  "urban",   20, 9.0,  True,  "low"   ),
        RoadConfig("entebbe_rd",  "Entebbe Road",  "highway", 40, 40.0, False, "low"   ),
        RoadConfig("n_bypass",    "N. Bypass",     "bypass",  30, 22.0, False, "low"   ),
    ]
}
