const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const API_KEY = import.meta.env.VITE_API_KEY || "";

async function request(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (API_KEY) headers["X-API-Key"] = API_KEY;

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json();
}

export const api = {
  getConfig: () => request("/api/config"),
  updateConfig: (payload) => request("/api/config", { method: "PUT", body: JSON.stringify(payload) }),
  getFixationCodes: () => request("/api/config/fixation-codes"),
  getDefectFrequencies: () => request("/api/config/defect-frequencies"),
  getStatus: () => request("/api/status"),
  getRul: () => request("/api/status/rul"),
  getSnapshots: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/api/history/snapshots${qs ? `?${qs}` : ""}`);
  },
  getSeveritySummary: (sinceMinutes) => {
    const qs = sinceMinutes ? `?since_minutes=${sinceMinutes}` : "";
    return request(`/api/history/severity-summary${qs}`);
  },
  getAlerts: (limit = 50) => request(`/api/history/alerts?limit=${limit}`),
  setDemoFault: (fault) => request("/api/realtime/demo-fault", { method: "POST", body: JSON.stringify({ fault }) }),
  getFaultOptions: () => request("/api/realtime/fault-options"),
};

export const WS_URL = (import.meta.env.VITE_WS_URL || "ws://localhost:8000") + "/api/realtime/ws";
