const BASE = import.meta.env.VITE_API_BASE || ''

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    ...init,
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
  signals: (symbol: string) => req<any>(`/api/signals?symbol=${symbol}`),
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
}

export function openTicks(symbol: string, onTick: (data: any) => void): () => void {
  const es = new EventSource(`${BASE}/api/sse/ticks?symbol=${encodeURIComponent(symbol)}`)
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
