const GLOW_COLORS = {
  purple: "#a855f7",
  blue: "#3b82f6",
  cyan: "#22d3ee",
  green: "#22c55e",
  orange: "#f97316",
  yellow: "#eab308",
  red: "#ef4444",
  pink: "#ec4899",
};

export default function Card({ title, subtitle, badge, icon: Icon, iconColor, glow, tight, className = "", children, style }) {
  const glowColor = GLOW_COLORS[glow] || null;
  return (
    <div className={`card ${tight ? "card--tight" : ""} ${className}`} style={style}>
      {glowColor && <div className="card__glow" style={{ background: glowColor }} />}
      {(title || badge) && (
        <div className="card__header">
          <div className="card__title">
            {Icon && (
              <span
                className="card__title-icon"
                style={{ background: `${GLOW_COLORS[iconColor] || glowColor || "#3b82f6"}22` }}
              >
                <Icon size={14} color={GLOW_COLORS[iconColor] || glowColor || "#60a5fa"} />
              </span>
            )}
            {title}
          </div>
          {badge && <span className="card__badge">{badge}</span>}
        </div>
      )}
      {subtitle && <p className="card__subtitle">{subtitle}</p>}
      {children}
    </div>
  );
}
