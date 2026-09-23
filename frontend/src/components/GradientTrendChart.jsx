import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
} from "recharts";

const PALETTE = {
  purple: "#a855f7",
  blue: "#3b82f6",
  cyan: "#22d3ee",
  green: "#22c55e",
  orange: "#f97316",
  yellow: "#eab308",
  red: "#ef4444",
};

function formatTime(t) {
  const d = new Date(t);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div
      style={{
        background: "#17152a",
        border: "1px solid rgba(255,255,255,0.1)",
        borderRadius: 10,
        padding: "0.6rem 0.8rem",
        fontSize: "0.75rem",
        boxShadow: "0 8px 24px rgba(0,0,0,0.4)",
      }}
    >
      <div style={{ color: "#9793ad", marginBottom: 4 }}>{formatTime(label)}</div>
      {payload.map((p) => (
        <div key={p.dataKey} style={{ color: p.color, fontWeight: 600 }}>
          {p.name}: {typeof p.value === "number" ? p.value.toFixed(2) : p.value}
        </div>
      ))}
    </div>
  );
}

/**
 * series: [{ key, name, color: paletteKey }]
 * data: array of objects with a `timestamp` field plus one field per series key
 * thresholds: optional [{ value, label, color }] horizontal reference lines
 */
export default function GradientTrendChart({ data, series, thresholds = [], yLabel, height = 260 }) {
  if (!data || data.length === 0) {
    return <div className="empty-state">Waiting for data…</div>;
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: -12 }}>
        <defs>
          {series.map((s) => (
            <linearGradient key={s.key} id={`grad-${s.key}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={PALETTE[s.color] || s.color} stopOpacity={0.35} />
              <stop offset="100%" stopColor={PALETTE[s.color] || s.color} stopOpacity={0} />
            </linearGradient>
          ))}
        </defs>
        <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />
        <XAxis
          dataKey="timestamp"
          tickFormatter={formatTime}
          stroke="#6b6880"
          fontSize={11}
          tickLine={false}
          axisLine={{ stroke: "rgba(255,255,255,0.08)" }}
          minTickGap={40}
        />
        <YAxis
          stroke="#6b6880"
          fontSize={11}
          tickLine={false}
          axisLine={false}
          label={yLabel ? { value: yLabel, angle: -90, position: "insideLeft", fill: "#6b6880", fontSize: 11 } : undefined}
        />
        <Tooltip content={<CustomTooltip />} />
        {series.length > 1 && <Legend wrapperStyle={{ fontSize: "0.72rem", color: "#9793ad" }} iconType="circle" iconSize={8} />}
        {thresholds.map((t) => (
          <ReferenceLine key={t.label} y={t.value} stroke={PALETTE[t.color] || t.color} strokeDasharray="4 4" strokeOpacity={0.6} />
        ))}
        {series.map((s) => (
          <Area
            key={s.key}
            type="monotone"
            dataKey={s.key}
            name={s.name}
            stroke={PALETTE[s.color] || s.color}
            strokeWidth={2.25}
            fill={`url(#grad-${s.key})`}
            dot={false}
            activeDot={{ r: 4 }}
            isAnimationActive={false}
          />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  );
}
