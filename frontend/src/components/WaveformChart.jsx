import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts";

export default function WaveformChart({ samples, sampleRateHz = 2048, height = 240 }) {
  if (!samples || samples.length === 0) {
    return <div className="empty-state">Waiting for time-domain signal…</div>;
  }

  const data = samples.map((v, i) => ({ t: +(i / sampleRateHz).toFixed(4), value: v }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: -12 }}>
        <defs>
          <linearGradient id="waveform-stroke" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#22d3ee" />
            <stop offset="100%" stopColor="#3b82f6" />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />
        <XAxis
          dataKey="t"
          type="number"
          domain={["dataMin", "dataMax"]}
          stroke="#6b6880"
          fontSize={11}
          tickLine={false}
          axisLine={{ stroke: "rgba(255,255,255,0.08)" }}
          label={{ value: "Time (s)", position: "insideBottom", offset: -2, fill: "#6b6880", fontSize: 11 }}
        />
        <YAxis stroke="#6b6880" fontSize={11} tickLine={false} axisLine={false} />
        <Tooltip
          contentStyle={{ background: "#17152a", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 10, fontSize: "0.75rem" }}
          labelFormatter={(v) => `${v} s`}
        />
        <Line type="monotone" dataKey="value" stroke="url(#waveform-stroke)" strokeWidth={1.75} dot={false} isAnimationActive={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
