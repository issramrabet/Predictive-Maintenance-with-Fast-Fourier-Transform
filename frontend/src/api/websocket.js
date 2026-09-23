import { useEffect, useRef, useState, useCallback } from "react";
import { WS_URL } from "./client";

const TREND_BUFFER_MAX = 120; // ~2 min at 1Hz broadcast, enough for on-dashboard sparklines

/**
 * Subscribes to the live analysis feed. Keeps the latest frame plus a
 * short in-memory rolling buffer for trend sparklines (the H-FFT/Dashboard
 * pages pull deeper history from /api/history/snapshots instead).
 */
export function useLiveFeed() {
  const [frame, setFrame] = useState(null);
  const [connected, setConnected] = useState(false);
  const [trend, setTrend] = useState([]);
  const wsRef = useRef(null);
  const retryTimer = useRef(null);

  const connect = useCallback(() => {
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => {
      setConnected(false);
      retryTimer.current = setTimeout(connect, 2000);
    };
    ws.onerror = () => ws.close();
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type !== "live_frame") return;
      setFrame(data);
      setTrend((prev) => {
        const next = [
          ...prev,
          {
            timestamp: data.timestamp,
            rms_x: data.rms_velocity_mm_s.x,
            rms_y: data.rms_velocity_mm_s.y,
            rms_z: data.rms_velocity_mm_s.z,
            temperature_c: data.temperature_c,
            crest_factor_x: data.crest_factor.x,
            kurtosis_x: data.kurtosis?.x,
            health_score: data.health_score,
          },
        ];
        return next.length > TREND_BUFFER_MAX ? next.slice(next.length - TREND_BUFFER_MAX) : next;
      });
    };
  }, []);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(retryTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { frame, connected, trend };
}
