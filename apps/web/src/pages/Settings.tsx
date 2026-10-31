import { useEffect, useState } from 'react'
import { api, setToken, getEngineBase, setEngineBase } from '../lib/api'

type Props = {
  status: any
  refreshStatus: () => void
  user: any | null
  onLogout: () => void
  onNeedLogin: () => void
}

export default function Settings({ status, refreshStatus, user, onLogout, onNeedLogin }: Props) {
  const [mode, setMode] = useState(status?.mode || 'paper')
  const [dsKey, setDsKey] = useState('')
  const [ds, setDs] = useState<any>(null)
  const [msg, setMsg] = useState('')
  const [outbound, setOutbound] = useState<any>(null)
  const [whitelist, setWhitelist] = useState('')
  const [engineUrl, setEngineUrl] = useState(() => getEngineBase())

  useEffect(() => {
    setMode(status?.mode || 'paper')
    api.deepseekStatus().then(setDs).catch(() => {})
    const ips = status?.binanceWhitelistIps || status?.binance?.whitelistIps || []
    if (Array.isArray(ips) && ips.length) setWhitelist(ips.join(', '))
    else api.getWhitelist().then((w) => setWhitelist(w.raw || '')).catch(() => {})
  }, [status])

  async function saveMode() {
    try {
      await api.setMode(mode)
      refreshStatus()
      setMsg(`Mode → ${mode}`)
    } catch (e: any) {
      setMsg(String(e.message || e))
    }
  }

  async function saveDeepseek() {
    try {
      const r = await api.setDeepseekKey(dsKey)
      setDs(await api.deepseekStatus())
      setDsKey('')
      setMsg(r.configured ? 'DeepSeek key saved (session)' : 'DeepSeek key cleared')
      refreshStatus()
    } catch (e: any) {
      setMsg(String(e.message || e))
    }
  }

  async function detectIp() {
    try {
      const r = await api.outboundIp()
      setOutbound(r)
      setMsg(r.ip ? `Outbound IP: ${r.ip}` : `Detect failed: ${r.error}`)
    } catch (e: any) {
      setMsg(String(e.message || e))
    }
  }

  async function saveWhitelist() {
    try {
      const r = await api.setWhitelist(whitelist)
      setWhitelist((r.ips || []).join(', '))
      refreshStatus()
      setMsg('Whitelist reminder saved（仍要去幣安後台貼同一組 IP）')
    } catch (e: any) {
      setMsg(String(e.message || e))
    }
  }

  function saveEngine() {
    setEngineBase(engineUrl.trim() || null)
    setMsg(engineUrl.trim() ? `Engine URL → ${engineUrl.trim().replace(/\/+$/, '')}` : 'Engine URL cleared（用同源／Vite proxy）')
    // Force reload so SSE reconnects with new base
    setTimeout(() => window.location.reload(), 400)
  }

  function logout() {
    setToken(null)
    onLogout()
  }

  const binanceOk = !!(status?.binance?.configured)
  const deepseekOk = !!(ds?.configured ?? status?.deepseek?.configured)
  const authOk = !!user

  return (
    <div className="grid cols-2">
      <div className="card" style={{ gridColumn: '1 / -1' }}>
        <h2>Connection status</h2>
        <div className="row-form">
          <span className={`status-dot ${authOk ? 'on' : 'off'}`}><i />Auth {authOk ? 'linked' : 'guest'}</span>
          <span className={`status-dot ${binanceOk ? 'on' : 'off'}`}><i />Binance {binanceOk ? 'keys set' : 'missing'}</span>
          <span className={`status-dot ${deepseekOk ? 'on' : 'off'}`}><i />DeepSeek {deepseekOk ? 'linked' : 'missing'}</span>
        </div>
        <p className="muted" style={{ marginTop: '0.5rem' }}>綠＝已連接／有 key；紅＝未登入或未設定。</p>
      </div>
      <div className="card" style={{ gridColumn: '1 / -1' }}>
        <h2>Engine URL（Android／遠端）</h2>
        <p className="muted">
          手機 APK 預設連唔到電腦 localhost。請喺電腦跑引擎（端口 8787），再填
          <code>http://你的電腦LAN_IP:8787</code>（同一 Wi‑Fi）。瀏覽器本機開發可留空。
        </p>
        <label className="field">API base
          <input value={engineUrl} onChange={(e) => setEngineUrl(e.target.value)} placeholder="http://192.168.1.10:8787" autoComplete="off" />
        </label>
        <div className="row-form" style={{ marginTop: '0.75rem' }}>
          <button className="primary" onClick={saveEngine}>Save & reload</button>
          <button type="button" onClick={() => { setEngineUrl(''); setEngineBase(null); setMsg('cleared'); setTimeout(() => window.location.reload(), 300) }}>Clear</button>
        </div>
      </div>

      <div className="card">
        <h2>Account</h2>
        {user ? (
          <>
            <p><strong>{user.displayName || user.email}</strong></p>
            <p className="muted">{user.email} · {user.provider}</p>
            <button onClick={logout}>登出</button>
          </>
        ) : (
          <>
            <p className="muted">訪客模式（紙上）</p>
            <button className="primary" onClick={onNeedLogin}>登入／註冊</button>
          </>
        )}
      </div>

      <div className="card">
        <h2>Trading mode</h2>
        <label className="field">Mode
          <select value={mode} onChange={(e) => setMode(e.target.value)}>
            <option value="paper">paper（預設）</option>
            <option value="live">live（需幣安 key；v0.1 stub）</option>
          </select>
        </label>
        <button className="primary" style={{ marginTop: '0.75rem' }} onClick={saveMode}>Apply</button>
        <p className="muted" style={{ marginTop: '0.75rem' }}>
          Binance configured: {String(status?.binance?.configured)} · {status?.binance?.note}
        </p>
        <p className="muted">Risk: min ${status?.minNotionalUsd} · max pos ${status?.maxPositionUsd} · daily loss ${status?.dailyLossLimitUsd}</p>
      </div>

      <div className="card">
        <h2>DeepSeek AI</h2>
        <p className="muted">Base URL: https://api.deepseek.com · 紙上模式可不填</p>
        <p>Configured: <strong>{String(ds?.configured ?? status?.deepseek?.configured)}</strong></p>
        <label className="field">DEEPSEEK_API_KEY（session；建議用 .env）
          <input type="password" value={dsKey} placeholder="sk-…" onChange={(e) => setDsKey(e.target.value)} autoComplete="off" />
        </label>
        <div className="row-form" style={{ marginTop: '0.75rem' }}>
          <button className="primary" onClick={saveDeepseek}>Save key</button>
          <button onClick={() => { setDsKey(''); api.setDeepseekKey('').then(() => api.deepseekStatus().then(setDs)) }}>Clear</button>
        </div>
      </div>

      <div className="card">
        <h2>幣安 API IP 白名單</h2>
        <p className="muted">
          喺幣安 → API 管理 → 編輯 → <strong>IP 存取限制</strong> 貼上引擎對外 IP。
          `.env` 嘅 <code>BINANCE_WHITELIST_IPS</code> 只係備忘，唔會代替幣安後台設定。
        </p>
        <div className="row-form">
          <button className="primary" onClick={detectIp}>偵測 outbound IP</button>
          {outbound?.ip && (
            <button type="button" onClick={() => navigator.clipboard?.writeText(outbound.ip)}>複製 {outbound.ip}</button>
          )}
        </div>
        {outbound && (
          <p className="muted" style={{ marginTop: '0.5rem' }}>
            {outbound.ip ? `Detected: ${outbound.ip}` : `Error: ${outbound.error}`}
          </p>
        )}
        <label className="field" style={{ marginTop: '0.75rem' }}>BINANCE_WHITELIST_IPS（逗號分隔）
          <input value={whitelist} onChange={(e) => setWhitelist(e.target.value)} placeholder="1.2.3.4, 5.6.7.8" />
        </label>
        <button style={{ marginTop: '0.5rem' }} onClick={saveWhitelist}>Save reminder</button>
      </div>

      {msg && <div className="toast" style={{ gridColumn: '1 / -1' }}>{msg}</div>}
    </div>
  )
}
