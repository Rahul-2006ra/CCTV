import { useState } from "react";
import { Bell, ArrowUpRight } from "lucide-react";
import { api, time } from "../services/api";
import InvestigationView from "../components/InvestigationView";
import type { Match } from "../types";
export default function Alerts({
  alerts,
  refresh,
}: {
  alerts: any[];
  refresh: () => void;
}) {
  const [selected, setSelected] = useState<Match | null>(null),
    [error, setError] = useState("");
  async function status(id: string, value: string) {
    try {
      await api(`/alerts/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ status: value }),
      });
      refresh();
    } catch (e) {
      setError((e as Error).message);
    }
  }
  if (selected)
    return (
      <InvestigationView match={selected} onClose={() => setSelected(null)} />
    );
  return (
    <>
      <div className="section-heading">
        <div>
          <p className="eyebrow">EVENTS / REVIEW QUEUE</p>
          <h1>Alerts</h1>
          <p className="subtitle">
            Rule-based candidates from indexed video tracks.
          </p>
        </div>
        <span className="badge">
          {alerts.filter((a) => a.status === "NEW").length} NEW
        </span>
      </div>
      <div className="note">
        Restricted zones use configured polygons. Rapid movement uses
        image-plane displacement. Unattended-object candidates require a
        stationary bag and no nearby detected person; they do not establish
        ownership.
      </div>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      {!alerts.length ? (
        <div className="empty panel">
          <Bell size={36} />
          <h3>No alerts detected.</h3>
          <p>Configure a camera zone and index footage to evaluate events.</p>
        </div>
      ) : (
        <div className="panel table-wrap">
          <table>
            <thead>
              <tr>
                <th>Event</th>
                <th>Camera</th>
                <th>Source timestamp</th>
                <th>Severity</th>
                <th>Status</th>
                <th>Footage</th>
              </tr>
            </thead>
            <tbody>
              {alerts.map((a) => (
                <tr key={a.id}>
                  <td>
                    <strong>{a.event_type}</strong>
                    <small>{a.details}</small>
                  </td>
                  <td className="mono">{a.camera_id}</td>
                  <td className="mono">{time(a.timestamp)}</td>
                  <td>
                    <span
                      className={
                        a.severity === "HIGH"
                          ? "severity-high"
                          : "severity-medium"
                      }
                    >
                      {a.severity}
                    </span>
                  </td>
                  <td>
                    <select
                      aria-label={`Status ${a.id}`}
                      value={a.status}
                      onChange={(e) => void status(a.id, e.target.value)}
                    >
                      {["NEW", "REVIEWED", "DISMISSED"].map((s) => (
                        <option key={s}>{s}</option>
                      ))}
                    </select>
                  </td>
                  <td>
                    <button
                      onClick={() =>
                        setSelected({
                          ...a,
                          start: a.timestamp,
                          end: a.timestamp,
                          object_type: "Rule-based event",
                          frame_path: "",
                        })
                      }
                    >
                      Review
                      <ArrowUpRight size={14} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
