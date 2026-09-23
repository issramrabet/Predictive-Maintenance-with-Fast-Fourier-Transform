export default function KpiTile({ label, value, unit, meta, tone }) {
  const toneClass = tone ? `severity-${tone}` : "";
  return (
    <div className="kpi-tile">
      <div className="kpi-tile__label">{label}</div>
      <div>
        <span className={`kpi-tile__value ${toneClass}`}>{value}</span>
        {unit ? <span className="kpi-tile__unit">{unit}</span> : null}
      </div>
      {meta ? <div className="kpi-tile__meta">{meta}</div> : null}
    </div>
  );
}
