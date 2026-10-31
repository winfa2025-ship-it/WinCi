import { useEffect, useState } from 'react'
import { api, DEFAULT_ENGINE_URL, getEngineBase, setEngineBase, setToken } from '../lib/api'
import { getGoogleIdToken } from '../lib/googleAuth'
import { getGoogleClientId, setGoogleClientIdLocal } from '../lib/googleClientId'
import { isNativeApp } from '../lib/platform'

type Props = {
  onAuthed: (user: any) => void
  onGuest: () => void
}

export default function Login({ onAuthed, onGuest }: Props) {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [msg, setMsg] = useState('')
  const [engineUrl, setEngineUrl] = useState(() => getEngineBase() || DEFAULT_ENGINE_URL)
  const [clientIdInput, setClientIdInput] = useState(() => getGoogleClientId())
  const [engineOk, setEngineOk] = useState<boolean | null>(null)
  const [engineGoogle, setEngineGoogle] = useState(false)
  const [busy, setBusy] = useState(false)
  const native = isNativeApp()
  const clientId = clientIdInput.trim()

  async function probeEngine(base?: string) {
    const b = (base ?? (getEngineBase() || DEFAULT_ENGINE_URL)).trim()
    if (!b) {
      setEngineOk(false)
      return
    }
    try {
      // Persist so subsequent calls and Settings share the same base
      if (!getEngineBase()) setEngineBase(b)
      const s = await api.googleStatus()
      setEngineOk(true)
      setEngineGoogle(!!s.configured)
    } catch (e: any) {
      setEngineOk(false)
      setEngineGoogle(false)
    }
  }

  useEffect(() => {
    const base = getEngineBase() || DEFAULT_ENGINE_URL
    if (base && !getEngineBase()) setEngineBase(base)
    if (base && !engineUrl) setEngineUrl(base)
    probeEngine(base)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function saveConnection() {
    setEngineBase(engineUrl.trim() || null)
    setGoogleClientIdLocal(clientIdInput.trim() || null)
    setMsg(
      [
        engineUrl.trim() ? `Engine → ${engineUrl.trim().replace(/\/+$/, '')}` : 'Engine URL 已清空',
        clientIdInput.trim() ? 'Google Client ID 已存本機' : '未設 Google Client ID（可用電郵／Demo）',
      ].join(' · '),
    )
    probeEngine(engineUrl.trim())
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true)
    setMsg('')
    try {
      if (native && !getEngineBase()) {
        throw new Error('請先確認 Engine URL（預設網站伺服器）並按「儲存連線」')
      }
      const r =
        mode === 'login'
          ? await api.login(email, password)
          : await api.register(email, password, name)
      setToken(r.accessToken)
      onAuthed(r.user)
    } catch (err: any) {
      setMsg(friendlyErr(err))
    } finally {
      setBusy(false)
    }
  }

  async function googleReal() {
    setBusy(true)
    setMsg('')
    try {
      setGoogleClientIdLocal(clientId || null)
      if (native && !getEngineBase()) {
        throw new Error('請先確認 Engine URL（預設網站伺服器）並按「儲存連線」')
      }
      if (!clientId) {
        throw new Error('請貼上 Google Web Client ID（下面欄位），或用電郵／Demo 登入')
      }
      // Sync Client ID to engine so token audience verifies
      try {
        await api.setGoogleClientId(clientId)
        setEngineGoogle(true)
      } catch {
        /* engine may be old; still try login */
      }
      const idToken = await getGoogleIdToken()
      const r = await api.google(idToken)
      setToken(r.accessToken)
      onAuthed(r.user)
    } catch (err: any) {
      setMsg(friendlyErr(err))
    } finally {
      setBusy(false)
    }
  }

  async function googleDemo() {
    setBusy(true)
    setMsg('')
    try {
      if (native && !getEngineBase()) {
        throw new Error('請先確認 Engine URL（預設網站伺服器）並按「儲存連線」')
      }
      const r = await api.google('demo')
      setToken(r.accessToken)
      onAuthed(r.user)
      setMsg(r.demo ? '已用 Demo 登入（本機假帳，唔係真 Google）' : '已登入')
    } catch (err: any) {
      setMsg(friendlyErr(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-wrap">
      <div className="card auth-card">
        <div className="brand" style={{ marginBottom: '0.5rem' }}>
          Win<span>Ci</span>
        </div>
        <h2>{mode === 'login' ? '登入' : '註冊'}</h2>
        <p className="muted">
          {native ? 'Android APK' : 'Web'} · 電郵／Google／Demo · 紙上預設 · 引擎預設網站伺服器
        </p>

        <div className="card" style={{ margin: '0.75rem 0', padding: '0.75rem', background: 'var(--panel2)' }}>
          <strong style={{ fontSize: '0.9rem' }}>連線（登入前必填）</strong>
          <label className="field">
            Engine URL
            <input
              value={engineUrl}
              onChange={(e) => setEngineUrl(e.target.value)}
              placeholder="https://sitemixhk.com/winci-api"
              autoComplete="off"
            />
          </label>
          <label className="field">
            Google Web Client ID（真 Google 先要）
            <input
              value={clientIdInput}
              onChange={(e) => setClientIdInput(e.target.value)}
              placeholder="xxxxx.apps.googleusercontent.com"
              autoComplete="off"
            />
          </label>
          <div className="row-form" style={{ marginTop: '0.5rem' }}>
            <button type="button" className="primary" onClick={saveConnection} disabled={busy}>
              儲存連線
            </button>
            <span className={`status-dot ${engineOk ? 'on' : 'off'}`}>
              <i />
              引擎 {engineOk === null ? '…' : engineOk ? 'OK' : '未連'}
              {engineGoogle ? ' · Google 已設' : ''}
            </span>
          </div>
        </div>

        <form onSubmit={submit}>
          {mode === 'register' && (
            <label className="field">
              顯示名
              <input value={name} onChange={(e) => setName(e.target.value)} placeholder="可選" />
            </label>
          )}
          <label className="field">
            電郵
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="username"
            />
          </label>
          <label className="field">
            密碼（最少 6 位）
            <input
              type="password"
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
            />
          </label>
          <div className="row-form" style={{ marginTop: '0.75rem' }}>
            <button className="primary" type="submit" disabled={busy}>
              {mode === 'login' ? '電郵登入' : '註冊'}
            </button>
            <button type="button" disabled={busy} onClick={() => setMode(mode === 'login' ? 'register' : 'login')}>
              {mode === 'login' ? '改註冊' : '改登入'}
            </button>
          </div>
        </form>

        <div id="winci-gis-btn" style={{ marginTop: '0.75rem', minHeight: clientId && !native ? 44 : 0 }} />

        <div className="row-form" style={{ marginTop: '1rem' }}>
          <button type="button" className="primary" disabled={busy || !clientId} onClick={googleReal}>
            Google 登入
          </button>
          <button type="button" disabled={busy} onClick={googleDemo}>
            Demo 登入
          </button>
          <button type="button" disabled={busy} onClick={onGuest}>
            訪客紙上
          </button>
        </div>
        <p className="muted" style={{ marginTop: '0.75rem', fontSize: '0.8rem' }}>
          Android 唔可以喺 WebView 彈 Google 登入窗。要用真 Google：建 OAuth Web + Android client（
          <code>com.winci.app</code>），貼 Web Client ID。未有 Client ID 請用電郵或 Demo。
        </p>
        {msg && <div className="toast">{msg}</div>}
      </div>
    </div>
  )
}

function friendlyErr(err: any): string {
  const raw = String(err?.message || err || '')
  if (/Failed to fetch|NetworkError|Load failed|fetch/i.test(raw)) {
    return '連唔到引擎。預設係網站伺服器 https://sitemixhk.com/winci-api；檢查網絡或喺連線欄改 URL。'
  }
  // FastAPI often returns JSON {"detail":"..."}
  try {
    const j = JSON.parse(raw)
    if (j?.detail) return typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail)
  } catch {}
  return raw
}
