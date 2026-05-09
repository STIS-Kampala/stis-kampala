import { useState } from "react";
import { useRoads, useModels, usePredict, usePredictionHistory } from "./hooks/useSTIS";
import type { RoadId, ModelName } from "./types/api";

const LABEL_COLOR = {
  high:   "var(--color-red)",
  medium: "var(--color-amber)",
  low:    "var(--color-green)",
};

export default function App() {
  const [road, setRoad]   = useState<RoadId>("jinja_rd");
  const [hour, setHour]   = useState(8);
  const [rain, setRain]   = useState(0);
  const [model, setModel] = useState<ModelName>("gradient_boosting");

  const { data: roads  } = useRoads();
  const { data: models } = useModels();
  const predict          = usePredict();
  const { history, push } = usePredictionHistory();

  function handlePredict() {
    predict.mutate(
      { road_id: road, hour, rain_mm: rain, model },
      { onSuccess: (result) => push(result) },
    );
  }

  return (
    <div style={{ padding: 16, maxWidth: 480, margin: "0 auto" }}>

      <div style={{ marginBottom: 16, borderBottom: "1px solid var(--color-border)", paddingBottom: 12 }}>
        <div style={{ fontSize: 20, fontWeight: 900, background: "linear-gradient(90deg, #fcdc04, #2dd4bf, #38bdf8)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
          🇺🇬 STIS
        </div>
        <div style={{ color: "var(--color-muted)", fontSize: 9, letterSpacing: 2 }}>
          SMART TRAFFIC INTELLIGENCE · KAMPALA · v3.0
        </div>
      </div>

      <div style={{ background: "var(--color-card)", border: "1px solid var(--color-border)", borderRadius: "var(--r-lg)", padding: 16, marginBottom: 12 }}>

        <div style={{ marginBottom: 12 }}>
          <div style={{ color: "var(--color-muted)", fontSize: 9, marginBottom: 6 }}>ROAD</div>
          {roads?.map((r) => (
            <div
              key={r.id}
              onClick={() => setRoad(r.id)}
              style={{
                background: road === r.id ? "rgba(56,189,248,0.1)" : "var(--color-surface)",
                border: `1px solid ${road === r.id ? "var(--color-blue)" : "var(--color-border)"}`,
                borderRadius: "var(--r-md)",
                padding: "7px 10px",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 8,
                marginBottom: 4,
              }}
            >
              <span style={{ color: LABEL_COLOR[r.label], fontSize: 8 }}>●</span>
              <span style={{ color: road === r.id ? "var(--color-blue)" : "var(--color-text)", fontSize: 10 }}>
                {r.name}
              </span>
              <span style={{ color: "var(--color-muted)", fontSize: 8, marginLeft: "auto" }}>
                {r.type} · {r.km}km
              </span>
            </div>
          ))}
        </div>

        <div style={{ marginBottom: 12 }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 5 }}>
            <span style={{ color: "var(--color-muted)", fontSize: 9 }}>HOUR</span>
            <span style={{ color: "var(--color-blue)", fontSize: 10, fontWeight: 700 }}>
              {String(hour).padStart(2, "0")}:00
              {[7,8,9].includes(hour) ? " 🌅 Rush AM" : [17,18,19,20].includes(hour) ? " 🌆 Rush PM" : hour < 5 || hour >= 23 ? " 🌙 Night" : ""}
            </span>
          </div>
          <input
            type="range" min={0} max={23} value={hour}
            onChange={(e) => setHour(Number(e.target.value))}
            style={{ width: "100%", accentColor: "var(--color-blue)" }}
          />
        </div>

        <div style={{ marginBottom: 12 }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 5 }}>
            <span style={{ color: "var(--color-muted)", fontSize: 9 }}>RAIN</span>
            <span style={{ color: "var(--color-blue)", fontSize: 10, fontWeight: 700 }}>
              {rain}mm {rain === 0 ? "☀️" : rain < 5 ? "🌦" : rain < 15 ? "🌧" : "⛈"}
            </span>
          </div>
          <input
            type="range" min={0} max={40} step={0.5} value={rain}
            onChange={(e) => setRain(Number(e.target.value))}
            style={{ width: "100%", accentColor: "var(--color-teal)" }}
          />
        </div>

        <div style={{ marginBottom: 12 }}>
          <div style={{ color: "var(--color-muted)", fontSize: 9, marginBottom: 6 }}>MODEL</div>
          <div style={{ display: "flex", gap: 5 }}>
            {models?.map((m) => (
              <button
                key={m.name}
                onClick={() => setModel(m.name)}
                style={{
                  flex: 1,
                  background: model === m.name ? "rgba(56,189,248,0.1)" : "var(--color-surface)",
                  border: `1px solid ${model === m.name ? "var(--color-blue)" : "var(--color-border)"}`,
                  color: model === m.name ? "var(--color-blue)" : "var(--color-muted)",
                  borderRadius: "var(--r-md)",
                  padding: "6px 4px",
                  cursor: "pointer",
                  fontSize: 8,
                  fontFamily: "var(--font-mono)",
                }}
              >
                {m.name === "gradient_boosting" ? "🚀 GB" : m.name === "random_forest" ? "🌲 RF" : "📐 Ridge"}
              </button>
            ))}
          </div>
        </div>

        <button
          onClick={handlePredict}
          disabled={predict.isPending}
          style={{
            width: "100%",
            padding: "11px 0",
            background: predict.isPending ? "var(--color-dim)" : "linear-gradient(135deg, var(--color-teal), var(--color-blue))",
            border: "none",
            borderRadius: "var(--r-md)",
            color: "#fff",
            fontSize: 11,
            fontWeight: 800,
            cursor: predict.isPending ? "not-allowed" : "pointer",
            fontFamily: "var(--font-mono)",
            letterSpacing: 2,
          }}
        >
          {predict.isPending ? "⏳ PREDICTING..." : "⚡ PREDICT"}
        </button>
      </div>

      {predict.data && (
        <div style={{
          background: "var(--color-card)",
          border: `1px solid ${LABEL_COLOR[predict.data.label]}44`,
          borderRadius: "var(--r-lg)",
          padding: 16,
          marginBottom: 12,
          textAlign: "center",
          animation: "fadeIn 0.25s ease forwards",
        }}>
          <div style={{ color: "var(--color-muted)", fontSize: 9 }}>{predict.data.road_name}</div>
          <div style={{ color: LABEL_COLOR[predict.data.label], fontSize: 38, fontWeight: 900 }}>
            {predict.data.label.toUpperCase()}
          </div>
          <div style={{ color: "var(--color-text)", fontSize: 22, fontWeight: 700 }}>
            {predict.data.travel_min} min
          </div>
          <div style={{ color: "var(--color-muted)", fontSize: 9 }}>
            delay x{predict.data.delay_ratio} · CI [{predict.data.ci_95.lower}, {predict.data.ci_95.upper}]
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(2,1fr)", gap: 8, marginTop: 12 }}>
            {[
              ["Confidence",    (predict.data.confidence * 100).toFixed(1) + "%", "var(--color-green)" ],
              ["Latency",       predict.data.latency_ms + "ms",                   "var(--color-teal)"  ],
              ["Accident Risk", predict.data.risk.accident + "/100",              "var(--color-red)"   ],
              ["Top SHAP",      predict.data.shap.top_feature,                    "var(--color-purple)"],
            ].map(([l, v, c]) => (
              <div key={l} style={{ background: "var(--color-surface)", borderRadius: "var(--r-md)", padding: "7px 10px", display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "var(--color-muted)", fontSize: 8 }}>{l}</span>
                <span style={{ color: c, fontSize: 9, fontWeight: 700 }}>{v}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {history.length > 0 && (
        <div style={{ background: "var(--color-card)", border: "1px solid var(--color-border)", borderRadius: "var(--r-lg)", padding: 16 }}>
          <div style={{ color: "var(--color-text)", fontSize: 11, fontWeight: 800, marginBottom: 10 }}>📜 Recent Predictions</div>
          {history.map((h, i) => (
            <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: i < history.length - 1 ? "1px solid var(--color-border)" : "none" }}>
              <span style={{ color: "var(--color-text)", fontSize: 9 }}>{h.road_name}</span>
              <span style={{ color: LABEL_COLOR[h.label], fontSize: 9, fontWeight: 700 }}>{h.label.toUpperCase()}</span>
              <span style={{ color: "var(--color-mid)", fontSize: 9 }}>{h.travel_min}min</span>
            </div>
          ))}
        </div>
      )}

    </div>
  );
}
