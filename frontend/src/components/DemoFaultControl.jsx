import { useEffect, useState } from "react";
import { api } from "../api/client";

export default function DemoFaultControl({ onChange }) {
  const [options, setOptions] = useState([]);
  const [selected, setSelected] = useState("healthy");
  const [error, setError] = useState(null);

  useEffect(() => {
    api
      .getFaultOptions()
      .then(setOptions)
      .catch((err) => setError(err.message));
  }, []);

  const handleChange = async (e) => {
    const value = e.target.value;
    setSelected(value);
    try {
      await api.setDemoFault(value === "healthy" ? null : value);
      onChange?.(value);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="field" style={{ maxWidth: 420 }}>
      <label className="field__label" htmlFor="demo-fault-select">
        Inject a simulated fault
      </label>
      <select id="demo-fault-select" className="select" value={selected} onChange={handleChange}>
        <option value="healthy">Normal operation (no fault)</option>
        {options
          .filter((o) => o.row !== "healthy")
          .map((o) => (
            <option key={o.row} value={o.row}>
              {o.label}
            </option>
          ))}
      </select>
      <span className="field__hint">
        Forces the simulator to reproduce a given defect signature, so you can exercise the dashboard without a physical sensor connected.
      </span>
      {error && <div className="notice notice--error">{error}</div>}
    </div>
  );
}
