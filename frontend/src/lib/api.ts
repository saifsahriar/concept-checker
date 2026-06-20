import { supabase } from './supabase';

const apiUrl = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8000';

async function getAccessToken() {
  if (!supabase) {
    return null;
  }
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token ?? null;
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = await getAccessToken();
  const headers = new Headers(init.headers);
  headers.set('Content-Type', 'application/json');
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(`${apiUrl}${path}`, {
    ...init,
    headers,
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    let message = `Request failed with ${response.status}`;
    if (payload?.detail) {
      if (typeof payload.detail === 'string') {
        message = payload.detail;
      } else if (Array.isArray(payload.detail)) {
        message = payload.detail.map((err: any) => err.msg || JSON.stringify(err)).join(', ');
      }
    }
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}
