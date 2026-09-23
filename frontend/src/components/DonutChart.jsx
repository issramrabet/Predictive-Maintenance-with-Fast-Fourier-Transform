import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from "recharts";

const COLOR_MAP = {
  purple: "#a855f7",
  blue: "#3b82f6",
  cyan: "#22d3ee",
  green: "#22c55e",
  orange: "#f97316",
  yellow: "#eab308",
  red: "#ef4444",
};

/**
 * slices: [{ label, value, color: paletteKey }]
 */
export default function DonutChart({ slices, centerLabel, height = 220 }) {
  const total = slices.reduce((sum, s) => sum + s.value, 0);
  if (total === 0) {
    return <div className="empty-state">No data yet.</div>;
  }
  const data = slices.filter((s) => s.value > 0);

  return (
    <div style={{ position: "relative" }}>
      <ResponsiveContainer width="100%" height={height}>
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="label"
            innerRadius="62%"
            outerRadius="88%"
            paddingAngle={3}
            stroke="none"
            isAnimationActive={false}
          >
            {data.map((s) => (
              <Cell key={s.label} fill={COLOR_MAP[s.color] || s.color} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{ background: "#17152a", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 10, fontSize: "0.75rem" }}
          />
          <Legend
            verticalAlign="bottom"
            height={28}
            iconType="circle"
            iconSize={8}
            wrapperStyle={{ fontSize: "0.72rem", color: "#9793ad" }}
          />
        </PieChart>
      </ResponsiveContainer>
      {centerLabel && (
        <div
          style={{
            position: "absolute",
            top: "42%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            textAlign: "center",
            pointerEvents: "none",
          }}
        >
          <div style={{ fontSize: "1.4rem", fontWeight: 700 }}>{total}</div>
          <div style={{ fontSize: "0.68rem", color: "#9793ad" }}>{centerLabel}</div>
        </div>
      )}
    </div>
  );
}
