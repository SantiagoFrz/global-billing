export type Paginated<T> = { count: number; next: string | null; previous: string | null; results: T[] };

let csrfToken: string | null = null;

async function getCsrf(): Promise<string> {
  if (csrfToken) return csrfToken;
  const response = await fetch("/api/v1/auth/csrf/", { credentials: "include" });
  if (!response.ok) throw new Error("No pudimos iniciar la sesión segura.");
  csrfToken = (await response.json()).csrfToken;
  return csrfToken!;
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !(init.body instanceof FormData)) headers.set("Content-Type", "application/json");
  if (init.method && !["GET", "HEAD"].includes(init.method.toUpperCase())) headers.set("X-CSRFToken", await getCsrf());
  const response = await fetch(path, { ...init, headers, credentials: "include" });
  if (response.status === 401 || response.status === 403) throw new Error("Tu sesión expiró. Vuelve a ingresar.");
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail ?? "No pudimos completar la operación.");
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}

export function formatCOP(value: number): string {
  return new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(value);
}

export function formatDate(value?: string | null): string {
  if (!value) return "—";
  return new Intl.DateTimeFormat("es-CO", { day: "2-digit", month: "short", year: "numeric", timeZone: "America/Bogota" }).format(new Date(value));
}

