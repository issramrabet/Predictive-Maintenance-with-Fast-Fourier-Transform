import { Routes, Route } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import { MachineConfigProvider } from "./context/MachineConfigContext";
import { LiveFeedProvider, useLiveFeedContext } from "./context/LiveFeedContext";
import DashboardPage from "./pages/DashboardPage";
import FFTAnalysisPage from "./pages/FFTAnalysisPage";
import HistoryPage from "./pages/HistoryPage";
import MachineConfigPage from "./pages/MachineConfigPage";

function Shell() {
  const { connected } = useLiveFeedContext();
  return (
    <div className="shell">
      <Sidebar connected={connected} />
      <div className="main">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/fft" element={<FFTAnalysisPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/config" element={<MachineConfigPage />} />
        </Routes>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <MachineConfigProvider>
      <LiveFeedProvider>
        <Shell />
      </LiveFeedProvider>
    </MachineConfigProvider>
  );
}
