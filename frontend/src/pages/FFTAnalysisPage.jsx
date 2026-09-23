import { useState } from "react";
import { AudioWaveform, Activity, ListChecks, Waves } from "lucide-react";
import { useLiveFeedContext } from "../context/LiveFeedContext";
import Card from "../components/Card";
import SpectrumChart from "../components/SpectrumChart";
import WaveformChart from "../components/WaveformChart";
import PeakTable from "../components/PeakTable";
import Badge from "../components/Badge";

export default function FFTAnalysisPage() {
  const { frame, connected } = useLiveFeedContext();
  const [selectedPeak, setSelectedPeak] = useState(null);

  const peaks = frame?.peaks || [];
  const spectrum = frame?.spectrum || [];

  return (
    <div>
      <div className="topbar">
        <div>
          <h1 className="topbar__title">H-FFT — Spectral Analysis</h1>
          <p className="topbar__subtitle">
            Spectrum computed live on the X axis (radial) — click a table row to see the peak detail
          </p>
        </div>
        <span className="status-pill">
          <span className="status-pill__dot" style={{ background: connected ? "#4ade80" : "#f87171" }} />
          {connected ? "Live feed" : "Disconnected"}
        </span>
      </div>

      <div className="grid">
        <div className="col-8">
          <Card
            title="H-FFT Spectrum"
            subtitle="Amplitude (mm/s²) vs. frequency (Hz) — red dots mark catalogued defect frequencies"
            icon={AudioWaveform}
            glow="blue"
          >
            <SpectrumChart spectrum={spectrum} peaks={peaks} />
          </Card>
        </div>
        <div className="col-4">
          <Card title="Selected Peak Detail" icon={Activity} glow="red">
            {selectedPeak ? (
              <div>
                <p style={{ fontWeight: 600, marginBottom: "0.6rem" }}>{selectedPeak.label}</p>
                <Badge severity={selectedPeak.severity} />
                <div
                  style={{
                    marginTop: "1rem",
                    padding: "0.85rem 1rem",
                    background: "rgba(255,255,255,0.03)",
                    border: "1px solid var(--border)",
                    borderRadius: "var(--radius-sm)",
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: "0.6rem",
                    fontSize: "0.82rem",
                  }}
                >
                  <span style={{ color: "var(--text-secondary)" }}>Frequency</span>
                  <strong>{selectedPeak.freq?.toFixed(2)} Hz</strong>
                  <span style={{ color: "var(--text-secondary)" }}>Measured amplitude</span>
                  <strong>{selectedPeak.amplitude?.toFixed(3)} mm/s²</strong>
                  <span style={{ color: "var(--text-secondary)" }}>Normal threshold</span>
                  <strong>{selectedPeak.v_normal} mm/s²</strong>
                  <span style={{ color: "var(--text-secondary)" }}>Danger threshold</span>
                  <strong>{selectedPeak.v_danger} mm/s²</strong>
                </div>
              </div>
            ) : (
              <div className="empty-state">Select a peak in the table below to see its detail.</div>
            )}
          </Card>
        </div>

        <div className="col-12">
          <Card
            title="Time-Domain Signal — X axis (raw)"
            subtitle="Most recent 400-sample window (2048 Hz sample rate)"
            icon={Waves}
            glow="cyan"
          >
            <WaveformChart samples={frame?.raw_waveform_x} />
          </Card>
        </div>

        <div className="col-12">
          <Card
            title="Frequency Peak Interpretation"
            subtitle="Reference used to diagnose a fault from a peak's position"
            icon={ListChecks}
            glow="purple"
          >
            <PeakTable peaks={peaks} onSelect={setSelectedPeak} selectedRow={selectedPeak?.row} />
          </Card>
        </div>
      </div>
    </div>
  );
}
