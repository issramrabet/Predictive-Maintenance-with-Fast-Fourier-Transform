import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import Card from "./Card";

export default function StatCard({ label, value, unit, meta, icon, glow, delta, deltaLabel }) {
  let DeltaIcon = Minus;
  let deltaClass = "delta-chip--flat";
  if (typeof delta === "number") {
    if (delta > 0) {
      DeltaIcon = TrendingUp;
      deltaClass = "delta-chip--up";
    } else if (delta < 0) {
      DeltaIcon = TrendingDown;
      deltaClass = "delta-chip--down";
    }
  }

  return (
    <Card title={label} icon={icon} iconColor={glow} glow={glow} tight>
      <div className="stat-card__value-row">
        <span className="stat-card__value">{value}</span>
        {unit ? <span className="stat-card__unit">{unit}</span> : null}
        {deltaLabel ? (
          <span className={`delta-chip ${deltaClass}`}>
            <DeltaIcon size={11} />
            {deltaLabel}
          </span>
        ) : null}
      </div>
      {meta ? <div className="stat-card__meta">{meta}</div> : null}
    </Card>
  );
}
