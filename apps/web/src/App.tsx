import { useEffect, useMemo, useState } from 'react'
import { api, getToken, openTicks, setToken } from './lib/api'
import Markets from './pages/Markets'
import Chart from './pages/Chart'
import OrderTicket from './pages/OrderTicket'
import Bots from './pages/Bots'
import Signals from './pages/Signals'
import Portfolio from './pages/Portfolio'
import Settings from './pages/Settings'
import Login from './pages/Login'
import TimeframePicker, { type Timeframe } from './components/TimeframePicker'

type Tab = 'markets' | 'chart' | 'order' | 'bots' | 'signals' | 'portfolio' | 'settings'

const TABS: { id: Tab; label: string }[] = [
  { id: 'markets', label: 'Markets' },
  { id: 'chart', label: 'Chart' },
  { id: 'order', label: 'Order' },
  { id: 'bots', label: 'Bots' },
  { id: 'signals', label: 'Signals 100' },
  { id: 'portfolio', label: 'Portfolio' },
  { id: 'settings', label: 'Settings' },
]

function StatusDot({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span className={`status-dot ${ok ? 'on' : 'off'}`} title={label}>
      <i />
      {label}
    </span>
  )
}

export default function App() {
  const [tab, setTab] = useState<Tab>('markets')
  const [symbol, setSymbol] = useState('BTCUSDT')
  const [timeframe, setTimeframe] = useState<Timeframe>('1m')
  const [tick, setTick] = useState<any>(null)
  const [signals, setSignals] = useState<any[]>([])
  const [status, setStatus] = useState<any>(null)
  const [err, setErr] = useState('')
  const [user, setUser] = useState<any | null>(null)
  const [authChecked, setAuthChecked] = useState(false)
  const [showLogin, setShowLogin] = useState(false)
  const [guest, setGuest] = useState(false)

  useEffect(() => {
    api.status().then((s) => {
      setStatus(s)
      if (s?.timeframe === '1m' || s?.timeframe === '5m' || s?.timeframe === '15m') {
        setTimeframe(s.timeframe)
      }
    }).catch((e) => setErr(String(e.message || e)))
    const t = getToken()
    if (!t) {
      setAuthChecked(true)
      setShowLogin(true)
      return
    }
    api.me()
      .then((u) => { setUser(u); setShowLogin(false); setGuest(false) })
      .catch(() => { setToken(null); setShowLogin(true) })
      .finally(() => setAuthChecked(true))
  }, [])

  useEffect(() => {
    if (showLogin && !guest && !user) return
    const stop = openTicks(symbol, setTick, timeframe)
    api.signals(symbol, timeframe).then((d) => setSignals(d.signals || [])).catch(() => {})
    const iv = setInterval(() => {
      api.signals(symbol, timeframe).then((d) => setSignals(d.signals || [])).catch(() => {})
    }, 15000)
    return () => { stop(); clearInterval(iv) }
  }, [symbol, timeframe, showLogin, guest, user])

  async function changeTf(tf: Timeframe) {
    setTimeframe(tf)
    try {
      const r = await api.setTimeframe(tf)
      setTick((prev: any) => prev ? { ...prev, timeframe: tf, bot: r.bot, autoearn: r.autoearn } : prev)
      api.status().then(setStatus).catch(() => {})
    } catch (e: any) {
      setErr(String(e.message || e))
    }
  }

  const mode = tick?.mode || status?.mode || 'paper'
  const consensus = tick?.consensus
  const portfolio = tick?.portfolio

  const binanceOk = !!(status?.binance?.configured)
  const deepseekOk = !!(tick?.deepseekConfigured ?? status?.deepseek?.configured)
  const authOk = !!user
  const botOk = !!(tick?.bot?.enabled || tick?.autoearn?.enabled)

  const body = useMemo(() => {
    const common = {
      symbol, setSymbol, timeframe, setTimeframe: changeTf,
      tick, signals, consensus, portfolio, status,
      refreshStatus: () => api.status().then(setStatus),
      user,
      onLogout: () => { setUser(null); setGuest(false); setShowLogin(true) },
      onNeedLogin: () => setShowLogin(true),
    }
    switch (tab) {
      case 'markets': return <Markets {...common} />
      case 'chart': return <Chart {...common} />
      case 'order': return <OrderTicket {...common} />
      case 'bots': return <Bots {...common} />
      case 'signals': return <Signals {...common} />
      case 'portfolio': return <Portfolio {...common} />
      case 'settings': return <Settings {...common} />
    }
  }, [tab, symbol, timeframe, tick, signals, consensus, portfolio, status, user])

  if (!authChecked) {
    return <div className="auth-wrap"><div className="muted">Loading…</div></div>
  }

  if (showLogin && !user && !guest) {
    return (
      <Login
        onAuthed={(u) => { setUser(u); setShowLogin(false); setGuest(false); api.status().then(setStatus) }}
        onGuest={() => { setGuest(true); setShowLogin(false) }}
      />
    )
  }

  return (
    <div className="app">
      <nav className="nav">
        <div className="brand">Win<span>Ci</span></div>
        {TABS.map((t) => (
          <button key={t.id} className={tab === t.id ? 'active' : ''} onClick={() => setTab(t.id)}>
            {t.label}
          </button>
        ))}
      </nav>
      <div className="main">
        <div className="topbar">
          <div>
            <strong>個人短炒儀表板</strong>
            <div className="muted" style={{ fontSize: '0.85rem' }}>
              {symbol} · {timeframe} · consensus {consensus?.score ?? '—'} · {consensus?.action ?? '—'}
              {user ? ` · ${user.email}` : ' · 訪客'}
            </div>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
            <TimeframePicker value={timeframe} onChange={changeTf} size="sm" label="短炒" />
            <span className={`pill ${mode === 'live' ? 'live' : 'paper'}`}>{mode.toUpperCase()}</span>
            <span className="pill">min $1</span>
            {portfolio?.killSwitch && <span className="pill live">KILL</span>}
            <StatusDot ok={authOk} label="Auth" />
            <StatusDot ok={binanceOk} label="Binance" />
            <StatusDot ok={deepseekOk} label="DeepSeek" />
            <StatusDot ok={botOk} label="Bot" />
          </div>
        </div>
        {err && <div className="toast">Engine: {err}（請先啟動 services/engine）</div>}
        {body}
      </div>
    </div>
  )
}
