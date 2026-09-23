import { useEffect, useState } from "react";
import { Settings2, CircleGauge, Loader2 } from "lucide-react";
import { useMachineConfig } from "../context/MachineConfigContext";
import Card from "../components/Card";
import NumberField from "../components/NumberField";
import SelectField from "../components/SelectField";
import DataTable from "../components/DataTable";

const FIELD_DEFAULTS = {
  N_rpm: 1500, n_balls: 8, Db_mm: 8, De_mm: 48, Di_mm: 32, phi_deg: 0,
  fixation: "B3", f_secteur_hz: 50, slip_pct: 3, gear_teeth: 20, pump_vanes: 6,
  power_kw: 75, foundation: "rigide",
};

const FOUNDATION_OPTIONS = [
  { value: "rigide", text: "Rigid (massive concrete base)" },
  { value: "souple", text: "Flexible (vibration-isolating mounts/springs)" },
];

const MOUNTING_COLUMNS = [
  { key: "code", header: "Code" },
  { key: "name", header: "Mounting" },
  { key: "orientation", header: "Orientation" },
  { key: "desc", header: "Explanation" },
];

export default function MachineConfigPage() {
  const { config, fixationCodes, defectFrequencies, updateConfig } = useMachineConfig();
  const [form, setForm] = useState(FIELD_DEFAULTS);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (config) {
      const { fr_hz, ...rest } = config;
      setForm(rest);
    }
  }, [config]);

  const set = (key) => (value) => setForm((f) => ({ ...f, [key]: value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSaveError(null);
    setSaved(false);
    try {
      await updateConfig(form);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      setSaveError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const frHz = form.N_rpm ? (form.N_rpm / 60).toFixed(2) : "—";
  const currentFamily = fixationCodes.find((c) => c.code === form.fixation)?.family;
  const fixationOptions = fixationCodes.map((c) => ({ value: c.code, text: `${c.code} — ${c.name}, ${c.orientation}` }));

  return (
    <div>
      <div className="topbar">
        <div>
          <h1 className="topbar__title">Motor Configuration</h1>
          <p className="topbar__subtitle">Update the values below — defect frequencies and amplitude thresholds recalculate automatically</p>
        </div>
      </div>

      <div className="grid">
        <div className="col-12">
          <Card icon={Settings2} glow="purple">
            <form onSubmit={handleSubmit}>
              <div className="readout-bar">
                Rotation frequency: f<sub>r</sub> = N / 60 = <strong style={{ color: "#d7bb1a" }}>{frHz} Hz</strong>
              </div>

              <div className="form-section">
                <div className="form-section__title">Rotation Speed</div>
                <div className="form-grid">
                  <NumberField id="N_rpm" label="N — Rotation speed (rpm)" value={form.N_rpm} step={1} min={1} onChange={set("N_rpm")} />
                </div>
              </div>

              <div className="form-section">
                <div className="form-section__title">Bearing Parameters</div>
                <div className="form-grid">
                  <NumberField id="n_balls" label="n — Number of balls" value={form.n_balls} step={1} min={1} onChange={set("n_balls")} />
                  <NumberField id="Db_mm" label="Db — Ball diameter (mm)" value={form.Db_mm} step={0.1} min={0.1} onChange={set("Db_mm")} />
                  <NumberField id="De_mm" label="De — Outer race diameter (mm)" value={form.De_mm} step={0.1} min={0.1} onChange={set("De_mm")} />
                  <NumberField id="Di_mm" label="Di — Inner race diameter (mm)" value={form.Di_mm} step={0.1} min={0.1} onChange={set("Di_mm")} />
                  <NumberField id="phi_deg" label="φ — Contact angle (°)" value={form.phi_deg} step={1} min={0} max={45} onChange={set("phi_deg")} />
                </div>
              </div>

              <div className="form-section">
                <div className="form-section__title">Motor Mounting</div>
                <div className="form-grid">
                  <SelectField id="fixation" label="Mounting mode (IEC 60034-7)" value={form.fixation} onChange={set("fixation")} options={fixationOptions} />
                </div>
                {currentFamily && (
                  <p className="field__hint" style={{ marginTop: "0.75rem" }}>
                    Associated defect family: <strong style={{ color: "#f4f3f9" }}>{currentFamily === "pattes" ? "feet (radial/vertical)" : "flange (axial)"}</strong>
                  </p>
                )}
              </div>

              <div className="form-section">
                <div className="form-section__title">Machine-Specific Parameters</div>
                <div className="form-grid">
                  <NumberField id="f_secteur_hz" label="f_mains — Mains frequency (Hz)" value={form.f_secteur_hz} step={1} min={1} onChange={set("f_secteur_hz")} />
                  <NumberField id="slip_pct" label="s — Slip (%)" value={form.slip_pct} step={0.1} min={0} max={100} onChange={set("slip_pct")} />
                  <NumberField id="gear_teeth" label="Z — Gear teeth count" value={form.gear_teeth} step={1} min={0} onChange={set("gear_teeth")} />
                  <NumberField id="pump_vanes" label="Nb — Pump impeller vanes" value={form.pump_vanes} step={1} min={0} onChange={set("pump_vanes")} />
                </div>
              </div>

              <div className="form-section">
                <div className="form-section__title">Alert Thresholds — ISO 20816-3</div>
                <div className="form-grid">
                  <NumberField id="power_kw" label="P — Motor power (kW)" value={form.power_kw} step={1} min={0.1} onChange={set("power_kw")} />
                  <SelectField id="foundation" label="Foundation type" value={form.foundation} onChange={set("foundation")} options={FOUNDATION_OPTIONS} />
                </div>
                {defectFrequencies && (
                  <p className="field__hint" style={{ marginTop: "0.75rem" }}>
                    Computed thresholds: zone B/C = <strong style={{ color: "#f4f3f9" }}>{defectFrequencies.v_normal} mm/s</strong> · zone C/D ={" "}
                    <strong style={{ color: "#f4f3f9" }}>{defectFrequencies.v_danger} mm/s</strong>
                  </p>
                )}
              </div>

              <button type="submit" className="btn btn--primary" disabled={saving}>
                {saving && <Loader2 size={15} className="spin" />}
                {saving ? "Saving…" : "Save configuration"}
              </button>

              {saved && <div className="notice notice--success">Configuration saved</div>}
              {saveError && <div className="notice notice--error">Failed to save: {saveError}</div>}
            </form>
          </Card>
        </div>

        <div className="col-12">
          <Card
            title="Motor Mounting Codes (IEC 60034-7)"
            subtitle='Reference for the codes available in the "Mounting mode" menu above'
            icon={CircleGauge}
            glow="cyan"
          >
            <DataTable columns={MOUNTING_COLUMNS} rows={fixationCodes} getRowId={(r) => r.code} />
          </Card>
        </div>
      </div>
    </div>
  );
}
