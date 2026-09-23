import { NavLink } from "react-router-dom";
import { Activity, AudioWaveform, History, SlidersHorizontal, Radio } from "lucide-react";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: Activity },
  { to: "/fft", label: "H-FFT Analysis", icon: AudioWaveform },
  { to: "/history", label: "History", icon: History },
  { to: "/config", label: "Motor Configuration", icon: SlidersHorizontal },
];

export default function Sidebar({ connected }) {
  return (
    <aside className="sidebar">
      <div className="sidebar__brand">
        <div className="sidebar__brand-mark">
          <Radio size={18} color="#fff" />
        </div>
        <div className="sidebar__brand-text">
          <div className="sidebar__brand-title">Vibration Monitor</div>
          <div className="sidebar__brand-sub">Predictive maintenance</div>
        </div>
      </div>

      <div className="sidebar__section-label">Monitoring</div>
      {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
        <NavLink
          key={to}
          to={to}
          end={to === "/"}
          className={({ isActive }) => `nav-item${isActive ? " active" : ""}`}
        >
          <Icon size={17} />
          {label}
        </NavLink>
      ))}

      <div className="sidebar__footer">
        <span
          className="sidebar__footer-dot"
          style={{ background: connected ? "#4ade80" : "#f87171" }}
        />
        {connected ? "Sensor connected" : "Disconnected"}
      </div>
    </aside>
  );
}
