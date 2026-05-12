import { useState, useEffect } from "react";
import { useRoads, useModels, usePredict, usePredictionHistory, useWeather } from "./hooks/useSTIS";
import type { RoadId, ModelName } from "./types/api";

export default function App() {
  const [road, setRoad]   = useState<RoadId>("jinja_rd");
  const [hour, setHour]   = useState(8);
  const [rain, setRain]   = useState(0);
  const [model, setModel] = useState<ModelName>("gradient_boosting");
  const [toast, setToast] = useState<{ msg: string; ico: string } | null>(null);

  const { data: roads,   isError: roadsErr } = useRoads();
  const { data: models  } = useModels();
  const { data: weather } = useWeather();
  const predict           = usePredict();
  const { history, push } = usePredictionHistory();

  function showToast(msg: string, ico = "✅") {
    setToast({ msg, ico });
    setTimeout(() => setToast(null), 2800);
  }

  function handlePredict() {
    predict.mutate(
      { road_id: road, hour, rain_mm: rain, model },
      {
        onSuccess: (result) => { push(result); showToast("Prediction complete", "✅"); },
        onError:   ()       => showToast("API error", "❌"),
      }
    );
  }

  const rushLbl = (h: number) => {
    if (h >= 7 && h <= 9)   return "🌅 Rush AM";
    if (h >= 12 && h <= 14) return "☀️ Midday";
    if (h >= 17 && h <= 20) return "🌆 Rush PM";
    if (h < 5 || h >= 23)   return "🌙 Night";
    return "🕐 Off-Peak";
  };

  const rainIco  = (mm: number) => mm === 0 ? "☀️" : mm < 20 ? "🌦" : mm < 50 ? "🌧" : "⛈";
  const dotColor = (label: string) => label === "high" ? "#ff2d6b" : label === "medium" ? "#ffb800" : "#39ff14";
  const lvlColor = (label: string) => label === "high" ? "#ff2d6b" : label === "medium" ? "#ffb800" : "#39ff14";

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@300;400;500;700&display=swap');
        *, *::before, *::after { margin:0; padding:0; box-sizing:border-box; }
        :root {
          --bg:#03040a; --s1:#080b14; --s2:#0d1120;
          --border:rgba(255,255,255,0.07); --border2:rgba(255,255,255,0.12);
          --c:#00ffe0; --c2:#ff2d6b; --c3:#6c63ff; --c4:#ffb800; --c5:#39ff14;
          --t1:#ffffff; --t2:rgba(255,255,255,0.55); --t3:rgba(255,255,255,0.25);
          --r:14px; --r2:20px;
        }
        html { scroll-behavior:smooth; }
        body { background:var(--bg); color:var(--t1); font-family:'DM Sans',sans-serif; min-height:100dvh; overflow-x:hidden; -webkit-font-smoothing:antialiased; }
        .bg-fx { position:fixed;inset:0;pointer-events:none;z-index:0;overflow:hidden; }
        .bg-orb { position:absolute;border-radius:50%;filter:blur(80px);opacity:0.12;animation:orbFloat 12s ease-in-out infinite alternate; }
        .bg-orb:nth-child(1){width:500px;height:500px;background:var(--c);top:-150px;left:-100px;}
        .bg-orb:nth-child(2){width:400px;height:400px;background:var(--c3);bottom:-100px;right:-80px;animation-delay:-4s;}
        .bg-orb:nth-child(3){width:300px;height:300px;background:var(--c2);top:50%;left:50%;transform:translate(-50%,-50%);animation-delay:-8s;}
        .bg-grid { position:absolute;inset:0;background-image:linear-gradient(rgba(0,255,224,0.025) 1px,transparent 1px),linear-gradient(90deg,rgba(0,255,224,0.025) 1px,transparent 1px);background-size:44px 44px; }
        @keyframes orbFloat{0%{transform:scale(1) translate(0,0)}100%{transform:scale(1.2) translate(30px,20px)}}
        @keyframes rise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
        @keyframes blink{0%,100%{opacity:1}50%{opacity:0.3}}
        @keyframes gradAnim{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}
        @keyframes fadeIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
        @keyframes toastIn{from{transform:translateX(-50%) translateY(80px)}to{transform:translateX(-50%) translateY(0)}}
        .app { position:relative;z-index:1;max-width:460px;margin:0 auto;padding:0 16px 60px; }
        .sec-hd { display:flex;align-items:center;gap:12px;margin:28px 0 10px;font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:0.25em;text-transform:uppercase;color:var(--t3); }
        .sec-hd::after{content:'';flex:1;height:1px;background:var(--border);}
        .sec-num { width:20px;height:20px;border-radius:50%;background:var(--border);display:grid;place-items:center;font-size:9px;color:var(--t3);flex-shrink:0; }
        .road-item { position:relative;overflow:hidden;display:flex;align-items:center;justify-content:space-between;padding:13px 16px;background:var(--s1);border:1px solid var(--border);border-radius:var(--r);cursor:pointer;margin-bottom:5px;transition:all 0.2s; }
        .road-item::before { content:'';position:absolute;left:0;top:0;bottom:0;width:3px;border-radius:0 3px 3px 0;background:transparent;transition:all 0.2s; }
        .road-item:hover{background:#0f1422;transform:translateX(3px);}
        .road-item.sel{background:rgba(0,255,224,0.05);border-color:rgba(0,255,224,0.22);box-shadow:0 0 30px rgba(0,255,224,0.1);}
        .road-item.sel::before{background:var(--c);box-shadow:0 0 10px var(--c);}
        .road-item.sel .rname{color:var(--c);}
        .param-card{background:var(--s1);border:1px solid var(--border);border-radius:var(--r2);padding:18px 20px;margin-bottom:10px;}
        .slider-wrap{position:relative;height:6px;margin-top:4px;}
        .slider-bg{position:absolute;inset:0;border-radius:100px;background:rgba(255,255,255,0.06);}
        .slider-prog{position:absolute;top:0;left:0;bottom:0;border-radius:100px;background:linear-gradient(90deg,var(--c3),var(--c));box-shadow:0 0 14px rgba(0,255,224,0.25);transition:width 0.05s;}
        .slider-prog.rain{background:linear-gradient(90deg,#1e6ef5,#5aacff);}
        .slider-knob{position:absolute;top:50%;transform:translate(-50%,-50%);width:22px;height:22px;border-radius:50%;background:#fff;box-shadow:0 0 0 3px rgba(0,255,224,0.25),0 3px 12px rgba(0,0,0,0.4);pointer-events:none;}
        .model-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:20px;}
        .model-card{background:var(--s1);border:1px solid var(--border);border-radius:var(--r);padding:16px 10px 14px;cursor:pointer;text-align:center;transition:all 0.2s;}
        .model-card:hover{background:#0f1422;}
        .model-card.sel{background:rgba(0,255,224,0.05);border-color:rgba(0,255,224,0.3);}
        .model-card.sel .mname{color:var(--c);}
        .predict-btn{width:100%;border:none;cursor:pointer;background:transparent;padding:0;border-radius:var(--r2);position:relative;font-family:'Bebas Neue',cursive;font-size:20px;letter-spacing:0.15em;color:var(--bg);transition:transform 0.15s;}
        .predict-btn::before{content:'';position:absolute;inset:0;border-radius:var(--r2);background:linear-gradient(135deg,var(--c) 0%,#00d4b0 40%,var(--c3) 100%);background-size:200% 200%;animation:gradAnim 3s ease infinite;}
        .predict-btn::after{content:'';position:absolute;inset:-3px;border-radius:calc(var(--r2)+3px);background:linear-gradient(135deg,var(--c),var(--c3));z-index:-1;opacity:0.35;filter:blur(15px);}
        .predict-btn:hover{transform:translateY(-3px);}
        .predict-btn:disabled{opacity:0.7;transform:none;cursor:not-allowed;}
        .predict-inner{position:relative;z-index:1;display:flex;align-items:center;justify-content:center;gap:10px;padding:20px;}
        .result-hero{background:var(--s1);border:1px solid var(--border);border-radius:var(--r2);padding:24px;animation:fadeIn 0.4s ease forwards;}
        .stat-box{background:rgba(255,255,255,0.03);border:1px solid var(--border);border-radius:12px;padding:14px;}
        .hist-item{display:flex;align-items:center;justify-content:space-between;padding:12px 16px;background:var(--s1);border:1px solid var(--border);border-radius:var(--r);margin-bottom:6px;}
        .toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%) translateY(80px);background:var(--s2);border:1px solid var(--border2);border-radius:100px;padding:12px 20px;font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--t1);letter-spacing:0.05em;display:flex;align-items:center;gap:8px;z-index:999;transition:transform 0.3s ease;white-space:nowrap;}
        .toast.show{transform:translateX(-50%) translateY(0);}
        .loader{position:fixed;inset:0;background:rgba(3,4,10,0.75);backdrop-filter:blur(6px);z-index:100;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:16px;}
        .loader-ring{width:52px;height:52px;border:2px solid rgba(0,255,224,0.1);border-top-color:var(--c);border-radius:50%;animation:spin 0.7s linear infinite;}
        @keyframes spin{to{transform:rotate(360deg)}}
        input[type=range]{-webkit-appearance:none;width:100%;height:6px;background:transparent;}
      `}</style>

      {/* BG */}
      <div className="bg-fx">
        <div className="bg-orb" /><div className="bg-orb" /><div className="bg-orb" />
        <div className="bg-grid" />
      </div>

      {/* LOADER */}
      {predict.isPending && (
        <div className="loader">
          <div className="loader-ring" />
          <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 11, letterSpacing: "0.2em", textTransform: "uppercase", color: "var(--c)", animation: "blink 1s ease infinite" }}>Running Model</div>
        </div>
      )}

      {/* TOAST */}
      <div className={`toast ${toast ? "show" : ""}`}>
        <span>{toast?.ico}</span>
        <span>{toast?.msg}</span>
      </div>

      <div className="app">

        {/* HEADER */}
        <header style={{ padding: "44px 0 28px" }}>
          <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
            <div>
              <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, letterSpacing: "0.3em", textTransform: "uppercase", color: "var(--c)", marginBottom: 6, display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ width: 16, height: 1, background: "var(--c)", display: "inline-block" }} />
                Kampala · v3.0
              </div>
              <div style={{ fontFamily: "'Bebas Neue',cursive", fontSize: 64, lineHeight: 0.9, background: "linear-gradient(160deg,#fff 0%,var(--c) 100%)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>STIS</div>
              <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, letterSpacing: "0.18em", textTransform: "uppercase", color: "var(--t3)", marginTop: 4 }}>Smart Traffic Intelligence System</div>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 6, background: roadsErr ? "rgba(255,45,107,0.07)" : "rgba(0,255,224,0.07)", border: `1px solid ${roadsErr ? "rgba(255,45,107,0.18)" : "rgba(0,255,224,0.18)"}`, borderRadius: 100, padding: "8px 14px", fontFamily: "'JetBrains Mono',monospace", fontSize: 10, letterSpacing: "0.15em", color: roadsErr ? "var(--c2)" : "var(--c)", textTransform: "uppercase", marginTop: 6 }}>
              <span style={{ width: 7, height: 7, borderRadius: "50%", background: roadsErr ? "var(--c2)" : "var(--c)", animation: "blink 1.6s ease-in-out infinite", display: "inline-block" }} />
              {roadsErr ? "Offline" : "Online"}
            </div>
          </div>

          {/* WEATHER */}
          <div style={{ marginTop: 16, display: "flex", gap: 8, flexWrap: "wrap" as const }}>
            {[
              ["🌡", weather?.temperature != null ? `${weather.temperature}°C` : "—"],
              ["💧", weather?.humidity    != null ? `${weather.humidity}%`     : "—"],
              ["🌧", weather?.rainfall    != null ? `${weather.rainfall}mm`    : "0mm"],
            ].map(([ico, val]) => (
              <div key={ico} style={{ display: "flex", alignItems: "center", gap: 6, background: "var(--s1)", border: "1px solid var(--border)", borderRadius: 10, padding: "8px 12px", fontFamily: "'JetBrains Mono',monospace", fontSize: 11, color: "var(--t2)" }}>
                <span style={{ fontSize: 14 }}>{ico}</span>
                <span style={{ color: "var(--t1)", fontWeight: 500 }}>{val}</span>
              </div>
            ))}
          </div>
        </header>

        {/* ROADS */}
        <div className="sec-hd"><span className="sec-num">01</span>Select Road</div>
        {roads?.map((r) => (
          <div key={r.id} className={`road-item ${road === r.id ? "sel" : ""}`} onClick={() => setRoad(r.id)}>
            <div style={{ display: "flex", alignItems: "center", gap: 11 }}>
              <span style={{ width: 8, height: 8, borderRadius: "50%", background: dotColor(r.label), boxShadow: `0 0 8px ${dotColor(r.label)}99`, flexShrink: 0, display: "inline-block" }} />
              <span className="rname" style={{ fontSize: 14, fontWeight: 600, color: "var(--t2)", transition: "color 0.2s" }}>{r.name}</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
              <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 9, textTransform: "uppercase", background: "rgba(255,255,255,0.05)", color: "var(--t3)", padding: "3px 7px", borderRadius: 5 }}>{r.type}</span>
              <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 11, color: "var(--t3)" }}>{r.km}km</span>
            </div>
          </div>
        ))}

        {/* PARAMS */}
        <div className="sec-hd"><span className="sec-num">02</span>Parameters</div>
        <div className="param-card">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
            <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, letterSpacing: "0.2em", textTransform: "uppercase", color: "var(--t3)" }}>Hour of Day</span>
            <span style={{ fontFamily: "'Bebas Neue',cursive", fontSize: 22, color: "var(--c)" }}>
              {String(hour).padStart(2, "0")}:00{" "}
              <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 9, background: "rgba(255,184,0,0.1)", border: "1px solid rgba(255,184,0,0.2)", color: "var(--c4)", padding: "3px 8px", borderRadius: 6 }}>{rushLbl(hour)}</span>
            </span>
          </div>
          <div className="slider-wrap">
            <div className="slider-bg" />
            <div className="slider-prog" style={{ width: `${(hour / 23) * 100}%` }} />
            <div className="slider-knob" style={{ left: `${(hour / 23) * 100}%` }} />
            <input type="range" style={{ position: "absolute", inset: "-10px 0", width: "100%", opacity: 0, cursor: "pointer", zIndex: 2 }} min={0} max={23} value={hour} onChange={(e) => setHour(Number(e.target.value))} />
          </div>
        </div>

        <div className="param-card">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
            <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, letterSpacing: "0.2em", textTransform: "uppercase", color: "var(--t3)" }}>Rainfall</span>
            <span style={{ fontFamily: "'Bebas Neue',cursive", fontSize: 22, color: "#5aacff" }}>
              {rain} <span style={{ fontSize: 14, fontWeight: 300, color: "var(--t3)" }}>mm</span> {rainIco(rain)}
            </span>
          </div>
          <div className="slider-wrap">
            <div className="slider-bg" />
            <div className="slider-prog rain" style={{ width: `${(rain / 40) * 100}%` }} />
            <div className="slider-knob" style={{ left: `${(rain / 40) * 100}%` }} />
            <input type="range" style={{ position: "absolute", inset: "-10px 0", width: "100%", opacity: 0, cursor: "pointer", zIndex: 2 }} min={0} max={40} step={0.5} value={rain} onChange={(e) => setRain(Number(e.target.value))} />
          </div>
        </div>

        {/* MODEL */}
        <div className="sec-hd"><span className="sec-num">03</span>ML Model</div>
        <div className="model-grid">
          {models?.map((m) => (
            <div key={m.name} className={`model-card ${model === m.name ? "sel" : ""}`} onClick={() => setModel(m.name)}>
              <span style={{ fontSize: 22, display: "block", marginBottom: 7 }}>
                {m.name === "gradient_boosting" ? "🚀" : m.name === "random_forest" ? "🌲" : "📐"}
              </span>
              <div className="mname" style={{ fontSize: 13, fontWeight: 700, color: "var(--t2)" }}>
                {m.name === "gradient_boosting" ? "GB" : m.name === "random_forest" ? "RF" : "Ridge"}
              </div>
              <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 8, color: "var(--t3)", marginTop: 3, textTransform: "uppercase" }}>
                {m.name === "gradient_boosting" ? "Gradient Boost" : m.name === "random_forest" ? "Random Forest" : "Linear Reg."}
              </div>
            </div>
          ))}
        </div>

        {/* PREDICT */}
        <button className="predict-btn" onClick={handlePredict} disabled={predict.isPending}>
          <div className="predict-inner">
            <span style={{ fontSize: 22 }}>{predict.isPending ? "⏳" : "⚡"}</span>
            {predict.isPending ? "Running Model..." : "Predict Traffic"}
          </div>
        </button>

        {/* RESULT */}
        {predict.data && (
          <>
            <div className="sec-hd" style={{ marginTop: 24 }}><span className="sec-num">04</span>Analysis</div>
            <div className="result-hero">
              <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 20 }}>
                <div>
                  <div style={{ fontFamily: "'Bebas Neue',cursive", fontSize: 28 }}>{predict.data.road_name}</div>
                  <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, color: "var(--t3)", marginTop: 4 }}>
                    {String(hour).padStart(2, "0")}:00 · {rain}mm · {model.replace(/_/g, " ").toUpperCase()}
                  </div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontFamily: "'Bebas Neue',cursive", fontSize: 32, color: lvlColor(predict.data.label), textShadow: `0 0 20px ${lvlColor(predict.data.label)}66` }}>
                    {predict.data.label.toUpperCase()}
                  </div>
                  <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 9, color: "var(--t3)" }}>Congestion</div>
                </div>
              </div>

              <div style={{ display: "flex", alignItems: "baseline", gap: 6, marginBottom: 6 }}>
                <span style={{ fontFamily: "'Bebas Neue',cursive", fontSize: 56, lineHeight: 1 }}>{predict.data.travel_min}</span>
                <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 14, color: "var(--t2)" }}>MIN</span>
              </div>
              <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, color: "var(--t3)" }}>
                delay ×{predict.data.delay_ratio} from base travel time
              </div>

              <div style={{ height: 1, background: "var(--border)", margin: "18px 0" }} />

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                {[
                  ["Confidence",    `${(predict.data.confidence * 100).toFixed(1)}%`, "var(--c)"],
                  ["Accident Risk", `${predict.data.risk.accident}/100`,               "var(--c2)"],
                  ["Latency",       `${predict.data.latency_ms}ms`,                    "var(--c5)"],
                  ["Top SHAP",      predict.data.shap.top_feature,                     "var(--c3)"],
                ].map(([l, v, c]) => (
                  <div key={l} className="stat-box">
                    <div style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 9, letterSpacing: "0.15em", textTransform: "uppercase", color: "var(--t3)", marginBottom: 6 }}>{l}</div>
                    <div style={{ fontFamily: "'Bebas Neue',cursive", fontSize: 22, color: c }}>{v}</div>
                  </div>
                ))}
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: 10, marginTop: 10 }}>
                <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 9, color: "var(--t3)", width: 60, flexShrink: 0 }}>95% CI</span>
                <div style={{ flex: 1, height: 5, background: "rgba(255,255,255,0.05)", borderRadius: 100, position: "relative" as const }}>
                  <div style={{ position: "absolute" as const, top: 0, bottom: 0, left: `${Math.min(predict.data.ci_95.lower / 3 * 100, 85)}%`, width: `${Math.min((predict.data.ci_95.upper - predict.data.ci_95.lower) / 3 * 100 + 12, 50)}%`, borderRadius: 100, background: "linear-gradient(90deg,var(--c3),var(--c))" }} />
                </div>
                <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, color: "var(--t2)", flexShrink: 0 }}>[{predict.data.ci_95.lower}, {predict.data.ci_95.upper}]</span>
              </div>

              <div style={{ background: "rgba(0,255,224,0.04)", border: "1px solid rgba(0,255,224,0.12)", borderLeft: "3px solid var(--c)", borderRadius: "0 12px 12px 0", padding: "14px 16px", fontSize: 13, lineHeight: 1.65, color: "var(--t2)", marginTop: 16 }}>
                {predict.data.label === "high"
                  ? <><strong style={{ color: "var(--c)" }}>{predict.data.road_name}</strong> has heavy congestion — <strong style={{ color: "var(--c)" }}>+{Math.round((predict.data.delay_ratio - 1) * 100)}%</strong> delay. Consider N. Bypass.</>
                  : predict.data.label === "medium"
                  ? <>Moderate traffic on <strong style={{ color: "var(--c)" }}>{predict.data.road_name}</strong>. Delay ×{predict.data.delay_ratio}. Off-peak recommended.</>
                  : <><strong style={{ color: "var(--c)" }}>{predict.data.road_name}</strong> flowing well. Minimal delays expected.</>}
              </div>
            </div>
          </>
        )}

        {/* HISTORY */}
        {history.length > 0 && (
          <>
            <div className="sec-hd"><span className="sec-num">05</span>Recent Predictions</div>
            {history.map((h, i) => (
              <div key={i} className="hist-item">
                <span style={{ fontSize: 13, fontWeight: 500, color: "var(--t2)" }}>{h.road_name}</span>
                <span style={{ fontFamily: "'Bebas Neue',cursive", fontSize: 14, color: lvlColor(h.label) }}>{h.label.toUpperCase()}</span>
                <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 11, color: "var(--t3)" }}>{h.travel_min}min</span>
              </div>
            ))}
          </>
        )}

      </div>
    </>
  );
}
