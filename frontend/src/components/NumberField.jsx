export default function NumberField({ id, label, value, onChange, step = 1, min, max, hint }) {
  return (
    <div className="field">
      <label className="field__label" htmlFor={id}>
        {label}
      </label>
      <input
        id={id}
        type="number"
        className="input"
        value={value}
        step={step}
        min={min}
        max={max}
        onChange={(e) => onChange(Number(e.target.value))}
      />
      {hint && <span className="field__hint">{hint}</span>}
    </div>
  );
}
