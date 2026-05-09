import type { ReactNode, CSSProperties } from "react";

const T = {
  card:    "#091220",
  border:  "#0f2240",
  text:    "#c8dff5",
  muted:   "#64849e",
  surface: "#070d1a",
};

export function Card({ children, glow, style }: {
  children: ReactNode;
  glow?:    string;
  style?:   CSSProperties;
}) {
  return (
    <div style={{
      background:    T.card,
      border:        `1px solid ${glow ? glow + "44" : T.border}`,
      borderRadius:  14,
      padding:       16,
      boxShadow:     glow ? `0 0 28px ${glow}14` : "none",
      ...style,
    }}>
      {children}
    </div>
  );
}

export function Badge({ text, color, size = 9 }: {
  text:   string;
  color:  string;
  size?:  number;
}) {
  return (
    <span style={{
      background:   color + "22",
      color,
      border:       `1px solid ${color}44`,
      borderRadius: 5,
      padding:      "2px 7px",
      fontSize:     size,
      fontWeight:   700,
      whiteSpace:   "nowrap",
      display:      "inline-block",
    }}>
      {text}
    </span>
  );
}

export function Skeleton({ h = 120 }: { h?: number }) {
  return (
    <div
      role="status"
      aria-label="Loading..."
      style={{
        height:     h,
        borderRadius: 10,
        background: "linear-gradient(90deg, #0f2240 25%, #0c1d3e 50%, #0f2240 75%)",
        backgroundSize: "200% 100%",
        animation:  "shimmer 1.5s infinite",
      }}
    />
  );
}

export function EmptyState({ icon, message }: {
  icon:    string;
  message: string;
}) {
  return (
    <div style={{
      textAlign: "center",
      padding:   "32px 16px",
      color:     T.muted,
      fontSize:  10,
    }}>
      <div style={{ fontSize: 28, marginBottom: 10 }}>{icon}</div>
      {message}
    </div>
  );
}

export function ChartTooltip({ active, payload, label }: {
  active?:  boolean;
  payload?: { name: string; value: number | string; color?: string }[];
  label?:   string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background:   T.surface,
      border:       `1px solid ${T.border}`,
      borderRadius: 8,
      padding:      "8px 12px",
    }}>
      {label && <div style={{ color: T.muted, fontSize: 9, marginBottom: 4 }}>{label}</div>}
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color ?? T.text, fontSize: 10 }}>
          {p.name}: {typeof p.value === "number" ? p.value.toFixed(4) : p.value}
        </div>
      ))}
    </div>
  );
}
