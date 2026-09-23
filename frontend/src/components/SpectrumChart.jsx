import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

export default function SpectrumChart({ spectrum, peaks, height = 320 }) {
  if (!spectrum || spectrum.length === 0) {
    return <div className="empty-state">Waiting for spectrum…</div>;
  }

  const peakPoints = (peaks || [])
    .filter((p) => p.freq > 0)
    .map((p) => ({ freq: p.freq, amplitude: p.amplitude, label: p.label }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={spectrum} margin={{ top: 8, right: 12, bottom: 0, left: -12 }}>
        <defs>
          <linearGradient id="spectrum-fill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.4} />
            <stop offset="100%" stopColor="#a855f7" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="spectrum-stroke" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#3b82f6" />
            <stop offset="100%" stopColor="#a855f7" />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />
        <XAxis
          dataKey="freq"
          type="number"
          domain={["dataMin", "dataMax"]}
          stroke="#6b6880"
          fontSize={11}
          tickLine={false}
          axisLine={{ stroke: "rgba(255,255,255,0.08)" }}
          label={{ value: "Frequency (Hz)", position: "insideBottom", offset: -2, fill: "#6b6880", fontSize: 11 }}
        />
        <YAxis
          stroke="#6b6880"
          fontSize={11}
          tickLine={false}
          axisLine={false}
          label={{ value: "Amplitude (mm/s²)", angle: -90, position: "insideLeft", fill: "#6b6880", fontSize: 11 }}
        />
        <Tooltip
          contentStyle={{ background: "#17152a", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 10, fontSize: "0.75rem" }}
          labelFormatter={(v) => `${v} Hz`}
        />
        <Area
          type="monotone"
          dataKey="amplitude"
          stroke="url(#spectrum-stroke)"
          strokeWidth={2}
          fill="url(#spectrum-fill)"
          dot={false}
          isAnimationActive={false}
          name="Spectrum"
        />
        <Scatter data={peakPoints} dataKey="amplitude" fill="#f87171" isAnimationActive={false} name="Catalogued peaks" />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
