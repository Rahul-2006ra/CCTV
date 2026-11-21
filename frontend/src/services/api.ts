export const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

export function apiUrl(path: string): string {
  const clean = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE}/api${clean}`;
}

export function mediaUrl(path: string): string {
  if (!path) return "";
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  const clean = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE}${clean}`;
}

export async function api<T = any>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(apiUrl(path), {
    ...options,
    headers:
      options.body instanceof FormData
        ? options.headers
        : { "Content-Type": "application/json", ...options.headers },
  });
  if (!response.ok) {
    const data = await response
      .json()
      .catch(() => ({ detail: response.statusText }));
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : data.detail?.map((e: any) => e.msg).join("; ") || "Request failed",
    );
  }
  return response.json();
}
export const post = <T = any>(path: string, body: unknown): Promise<T> =>
  api<T>(path, { method: "POST", body: JSON.stringify(body) });
export function time(seconds: number = 0, precise = false) {
  return new Date(Math.max(0, seconds) * 1000).toISOString().slice(11, precise ? 23 : 19);
}
