import { useEffect, useState } from 'react'
import { api, setToken } from '../lib/api'

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
  const [googleConfigured, setGoogleConfigured] = useState(false)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    api.googleStatus().then((s) => setGoogleConfigured(!!s.configured)).catch(() => {})
  }, [])

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true)
    setMsg('')
    try {
      const r = mode === 'login'
        ? await api.login(email, password)
        : await api.register(email, password, name)
      setToken(r.accessToken)
      onAuthed(r.user)
    } catch (err: any) {
      setMsg(String(err.message || err))
    } finally {
      setBusy(false)
    }
  }

  async function googleDemo() {
    setBusy(true)
    setMsg('')
    try {
      // Real GIS when client id set: load script; otherwise demo credential
      const clientId = (import.meta as any).env?.VITE_GOOGLE_CLIENT_ID || ''
      if (clientId && googleConfigured && (window as any).google?.accounts?.id) {
        setMsg('請用 Google 彈窗完成登入')
        ;(window as any).google.accounts.id.initialize({
          client_id: clientId,
          callback: async (resp: any) => {
            try {
              const r = await api.google(resp.credential)
              setToken(r.accessToken)
              onAuthed(r.user)
            } catch (err: any) {
              setMsg(String(err.message || err))
            }
          },
        })
        ;(window as any).google.accounts.id.prompt()
      } else {
        const r = await api.google('demo')
        setToken(r.accessToken)
        onAuthed(r.user)
        if (r.demo) setMsg('Demo Google 登入（未設 GOOGLE_CLIENT_ID）')
      }
    } catch (err: any) {
      setMsg(String(err.message || err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-wrap">
      <div className="card auth-card">
        <div className="brand" style={{ marginBottom: '0.5rem' }}>Win<span>Ci</span></div>
        <h2>{mode === 'login' ? '登入' : '註冊'}</h2>
        <p className="muted">電郵密碼（本機 JWT）· Google（有 Client ID 用真登入，否則 Demo）</p>
        <form onSubmit={submit}>
          {mode === 'register' && (
            <label className="field">顯示名
              <input value={name} onChange={(e) => setName(e.target.value)} placeholder="可選" />
            </label>
          )}
          <label className="field">電郵
            <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="username" />
          </label>
          <label className="field">密碼（最少 6 位）
            <input type="password" required minLength={6} value={password} onChange={(e) => setPassword(e.target.value)} autoComplete={mode === 'login' ? 'current-password' : 'new-password'} />
          </label>
          <div className="row-form" style={{ marginTop: '0.75rem' }}>
            <button className="primary" type="submit" disabled={busy}>{mode === 'login' ? '登入' : '註冊'}</button>
            <button type="button" disabled={busy} onClick={() => setMode(mode === 'login' ? 'register' : 'login')}>
              {mode === 'login' ? '改註冊' : '改登入'}
            </button>
          </div>
        </form>
        <div className="row-form" style={{ marginTop: '1rem' }}>
          <button type="button" disabled={busy} onClick={googleDemo}>
            {googleConfigured ? 'Google 登入' : 'Demo Google 登入'}
          </button>
          <button type="button" disabled={busy} onClick={onGuest}>繼續訪客紙上模式</button>
        </div>
        {msg && <div className="toast">{msg}</div>}
      </div>
    </div>
  )
}
