function scoreColor(score) {
  if (score >= 70) return { from: "#22c55e", to: "#4ade80" };
  if (score >= 30) return { from: "#eab308", to: "#facc15" };
  return { from: "#ef4444", to: "#f87171" };
}

export default function HealthGauge({ score, size = 200 }) {
  if (typeof score !== "number") {
    return <div className="empty-state">Waiting for data…</div>;
  }

  const clamped = Math.max(0, Math.min(100, score));
  const radius = 80;
  const cx = 100;
  const cy = 100;
  const startAngle = 180;
  const endAngle = 0;
  const angle = startAngle - (clamped / 100) * (startAngle - endAngle);

  const toXY = (deg) => {
    const rad = (deg * Math.PI) / 180;
    return [cx + radius * Math.cos(rad), cy - radius * Math.sin(rad)];
  };

  const [startX, startY] = toXY(startAngle);
  const [endX, endY] = toXY(endAngle);
  const [valX, valY] = toXY(angle);

  const trackPath = `M ${startX} ${startY} A ${radius} ${radius} 0 0 1 ${endX} ${endY}`;
  // Semi-gauge: the sweep from 180° to any point between 180° and 0° is
  // always <=180°, so the large-arc-flag must always be 0 — a conditional
  // flag here draws the reflex (long way around) arc instead, which shows
  // up as the arc appearing to wrap the wrong way / split in two.
  const valuePath = `M ${startX} ${startY} A ${radius} ${radius} 0 0 1 ${valX} ${valY}`;
  const colors = scoreColor(clamped);
  const gradId = `gauge-grad-${Math.round(clamped)}`;

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
      <svg viewBox="0 0 200 115" width={size} height={size * 0.575}>
        <defs>
          <linearGradient id={gradId} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor={colors.from} />
            <stop offset="100%" stopColor={colors.to} />
          </linearGradient>
        </defs>
        <path d={trackPath} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth={16} strokeLinecap="round" />
        <path d={valuePath} fill="none" stroke={`url(#${gradId})`} strokeWidth={16} strokeLinecap="round" />
      </svg>
      <div style={{ fontSize: "2.1rem", fontWeight: 700, marginTop: "-0.6rem", letterSpacing: "-0.02em" }}>
        {clamped.toFixed(1)}
      </div>
      <div style={{ fontSize: "0.72rem", color: "#9793ad" }}>out of 100</div>
    </div>
  );
}
