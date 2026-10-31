const ENGINE_KEY = 'winci_engine_url'
const TOKEN_KEY = 'winci_token'

/** API base: Settings override → VITE_API_BASE → '' (same-origin / Vite proxy). */
export function getEngineBase(): string {
  try {
    const saved = localStorage.getItem(ENGINE_KEY)
    if (saved != null && saved.trim() !== '') return saved.trim().replace(/\/+$/, '')
  } catch {}
  const env = (import.meta.env.VITE_API_BASE as string | undefined) || ''
  return env.replace(/\/+$/, '')
}

export function setEngineBase(url: string | null) {
  try {
    if (url == null || url.trim() === '') localStorage.removeItem(ENGINE_KEY)
    else localStorage.setItem(ENGINE_KEY, url.trim().replace(/\/+$/, ''))
  } catch {}
}

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function setToken(token: string | null) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token)
    else localStorage.removeItem(TOKEN_KEY)
  } catch {}
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(init?.headers as Record<string, string> || {}),
  }
  if (token) headers.Authorization = `Bearer ${token}`
  const BASE = getEngineBase()
  const r = await fetch(`${BASE}${path}`, {
    ...init,
    headers,
  })
  if (!r.ok) {
    const t = await r.text()
    throw new Error(t || r.statusText)
  }
  return r.json()
}

export const api = {
  status: () => req<any>('/api/status'),
  markets: () => req<any[]>('/api/markets'),
  signals: (symbol: string, timeframe?: string) =>
    req<any>(`/api/signals?symbol=${encodeURIComponent(symbol)}${timeframe ? `&timeframe=${encodeURIComponent(timeframe)}` : ''}`),
  getTimeframe: () => req<any>('/api/timeframe'),
  setTimeframe: (timeframe: string) =>
    req<any>('/api/timeframe', { method: 'POST', body: JSON.stringify({ timeframe }) }),
  candles: (symbol: string, timeframe?: string, limit = 60) =>
    req<any>(
      `/api/candles?symbol=${encodeURIComponent(symbol)}&limit=${limit}${timeframe ? `&timeframe=${encodeURIComponent(timeframe)}` : ''}`,
    ),
  portfolio: () => req<any>('/api/portfolio'),
  orders: () => req<any>('/api/orders'),
  order: (body: any) => req<any>('/api/order', { method: 'POST', body: JSON.stringify(body) }),
  bots: () => req<any>('/api/bots'),
  patchBot: (id: string, body: any) =>
    req<any>(`/api/bots/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  resetKill: () => req<any>('/api/kill-switch/reset', { method: 'POST' }),
  setMode: (mode: string) =>
    req<any>('/api/settings/mode', { method: 'POST', body: JSON.stringify({ mode }) }),
  deepseekStatus: () => req<any>('/api/deepseek/status'),
  setDeepseekKey: (api_key: string) =>
    req<any>('/api/deepseek/key', { method: 'POST', body: JSON.stringify({ api_key }) }),
  commentary: (symbol: string, include_boost = false) =>
    req<any>('/api/deepseek/commentary', {
      method: 'POST',
      body: JSON.stringify({ symbol, include_boost }),
    }),
  register: (email: string, password: string, display_name = '') =>
    req<any>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, display_name }),
    }),
  login: (email: string, password: string) =>
    req<any>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  google: (credential = 'demo') =>
    req<any>('/auth/google', {
      method: 'POST',
      body: JSON.stringify({ credential }),
    }),
  me: () => req<any>('/auth/me'),
  googleStatus: () => req<any>('/auth/google/status'),
  outboundIp: () => req<any>('/api/binance/outbound-ip'),
  getWhitelist: () => req<any>('/api/binance/whitelist'),
  setWhitelist: (ips: string) =>
    req<any>('/api/binance/whitelist', {
      method: 'POST',
      body: JSON.stringify({ ips }),
    }),
}

export function openTicks(symbol: string, onTick: (data: any) => void, timeframe?: string): () => void {
  const qs = new URLSearchParams({ symbol })
  if (timeframe) qs.set('timeframe', timeframe)
  const BASE = getEngineBase()
  const es = new EventSource(`${BASE}/api/sse/ticks?${qs.toString()}`)
  es.addEventListener('tick', (ev) => {
    try {
      onTick(JSON.parse((ev as MessageEvent).data))
    } catch {}
  })
  es.onerror = () => {
    /* browser auto-reconnects */
  }
  return () => es.close()
}
