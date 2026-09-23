import { createContext, useContext } from "react";
import { useLiveFeed } from "../api/websocket";

const LiveFeedContext = createContext(null);

export function LiveFeedProvider({ children }) {
  const value = useLiveFeed();
  return <LiveFeedContext.Provider value={value}>{children}</LiveFeedContext.Provider>;
}

export function useLiveFeedContext() {
  const ctx = useContext(LiveFeedContext);
  if (!ctx) throw new Error("useLiveFeedContext must be used within LiveFeedProvider");
  return ctx;
}
