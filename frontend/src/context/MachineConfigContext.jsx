import { createContext, useContext, useCallback, useEffect, useState } from "react";
import { api } from "../api/client";

const MachineConfigContext = createContext(null);

export function MachineConfigProvider({ children }) {
  const [config, setConfig] = useState(null);
  const [fixationCodes, setFixationCodes] = useState([]);
  const [defectFrequencies, setDefectFrequencies] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [cfg, codes, defects] = await Promise.all([
        api.getConfig(),
        api.getFixationCodes(),
        api.getDefectFrequencies(),
      ]);
      setConfig(cfg);
      setFixationCodes(codes);
      setDefectFrequencies(defects);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const updateConfig = useCallback(async (payload) => {
    const cfg = await api.updateConfig(payload);
    setConfig(cfg);
    const defects = await api.getDefectFrequencies();
    setDefectFrequencies(defects);
    return cfg;
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <MachineConfigContext.Provider
      value={{ config, fixationCodes, defectFrequencies, loading, error, refresh, updateConfig }}
    >
      {children}
    </MachineConfigContext.Provider>
  );
}

export function useMachineConfig() {
  const ctx = useContext(MachineConfigContext);
  if (!ctx) throw new Error("useMachineConfig must be used within MachineConfigProvider");
  return ctx;
}
