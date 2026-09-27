import { useCallback, useEffect, useState } from "react";
import {
  Shield,
  LayoutDashboard,
  ScanLine,
  Film,
  Video,
  Bell,
  HardDrive,
} from "lucide-react";
import { api } from "./services/api";
import type { Camera, Video as VideoType } from "./types";
import Investigation from "./pages/Investigation";
import Footage from "./pages/Footage";
import Cameras from "./pages/Cameras";
import Alerts from "./pages/Alerts";
import Dashboard from "./pages/Dashboard";
import { ErrorBoundary } from "./components/ErrorBoundary";
const routes: Record<string, string> = {
  Dashboard: "/dashboard",
  Investigation: "/investigation",
  Footage: "/footage",
  Cameras: "/cameras",
  Alerts: "/alerts",
};
const currentPage = () =>
  Object.keys(routes).find((k) => routes[k] === window.location.pathname) ||
  "Investigation";
const nav = [
  ["Dashboard", LayoutDashboard],
  ["Investigation", ScanLine],
  ["Footage", Film],
  ["Cameras", Video],
  ["Alerts", Bell],
] as const;
export default function App() {
  const [page, setPageState] = useState(currentPage),
    [health, setHealth] = useState<any>(null),
    [cameras, setCameras] = useState<Camera[]>([]),
    [videos, setVideos] = useState<VideoType[]>([]),
    [alerts, setAlerts] = useState<any[]>([]),
    [dashboard, setDashboard] = useState<any>(null),
    [error, setError] = useState(""),
    [initial, setInitial] = useState<any>(null),
    [searchKey, setSearchKey] = useState(0);
  function setPage(value: string) {
    setPageState(value);
    if (window.location.pathname !== routes[value])
      window.history.pushState({}, "", routes[value]);
  }
  useEffect(() => {
    const update = () => setPageState(currentPage());
    window.addEventListener("popstate", update);
    return () => window.removeEventListener("popstate", update);
  }, []);
  const refresh = useCallback(async () => {
    try {
      const [h, c, v, a, d] = await Promise.all([
        api("/system/health"),
        api("/cameras"),
        api("/videos"),
        api("/alerts"),
        api("/dashboard"),
      ]);
      setHealth(h);
      setCameras(c);
      setVideos(v);
      setAlerts(a);
      setDashboard(d);
      setError("");
    } catch (e) {
      setHealth(null);
      setError((e as Error).message);
    }
  }, []);
  useEffect(() => {
    void refresh();
    const timer = setInterval(refresh, 2500);
    return () => clearInterval(timer);
  }, [refresh]);
  async function openSearch(id: string) {
    try {
      setInitial(await api(`/search/${id}`));
      setSearchKey((k) => k + 1);
      setPage("Investigation");
    } catch (e) {
      setError((e as Error).message);
    }
  }
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <Shield size={24} />
          </div>
          <div>
            CCTV<span>INTELLIGENCE</span>
          </div>
        </div>
        <p className="nav-label">WORKSPACE</p>
        <nav>
          {nav.map(([label, Icon]) => (
            <button
              aria-label={label}
              title={label}
              className={page === label ? "active" : ""}
              key={label}
              onClick={() => setPage(label)}
            >
              <Icon size={18} />
              <span>{label}</span>
              {label === "Alerts" && alerts.some((a) => a.status === "NEW") && (
                <b>{alerts.filter((a) => a.status === "NEW").length}</b>
              )}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <HardDrive size={17} />
          <div>
            Local workspace<small>Footage stays on your device</small>
          </div>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <span>
            WORKSPACE <span className="slash">/</span> <strong>{page}</strong>
          </span>
          <div>
            <span className={`dot ${health ? "" : "offline"}`} />
            {health ? "System online" : "Connecting"}
            <span className="divider" />
            {health?.device || "Local device"}
            <span className="badge">
              {health?.acceleration?.toUpperCase() || "—"}
            </span>
          </div>
        </header>
        <main>
          <ErrorBoundary>
            {error && (
              <div role="alert" className="error">
                Backend connection: {error}. Check that the backend is running on
                port 8000.
              </div>
            )}
            {page === "Dashboard" && (
              <Dashboard
                data={dashboard}
                health={health}
                navigate={setPage}
                openSearch={openSearch}
              />
            )}
            <div hidden={page !== "Investigation"}>
              <Investigation
                key={searchKey}
                cameras={cameras}
                initial={initial}
                onInitialConsumed={() => setInitial(null)}
              />
            </div>
            {page === "Footage" && (
              <Footage
                cameras={cameras}
                videos={videos}
                refresh={refresh}
                onInvestigate={(q, cid, vid, fname) => {
                  setInitial({
                    query: q || "",
                    camera_id: cid,
                    video_id: vid,
                    video_filename: fname,
                    clues: q ? [q] : [],
                  });
                  setSearchKey((k) => k + 1);
                  setPage("Investigation");
                }}
              />
            )}{" "}
            {page === "Cameras" && (
              <Cameras cameras={cameras} refresh={refresh} />
            )}{" "}
            {page === "Alerts" && <Alerts alerts={alerts} refresh={refresh} />}
          </ErrorBoundary>
        </main>
        <footer className="app-footer">
          <span>
            CCTV INTELLIGENCE <span className="muted">/ LOCAL PROTOTYPE</span>
          </span>
          <span>No facial recognition · No identity inference</span>
        </footer>
      </div>
    </div>
  );
}
