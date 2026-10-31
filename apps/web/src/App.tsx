import { useEffect, useMemo, useState } from 'react'
import { api, openTicks } from './lib/api'
import Markets from './pages/Markets'
import Chart from './pages/Chart'
import OrderTicket from './pages/OrderTicket'
import Bots from './pages/Bots'
import Signals from './pages/Signals'
import Portfolio from './pages/Portfolio'
import Settings from './pages/Settings'

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

export default function App() {
  const [tab, setTab] = useState<Tab>('markets')
  const [symbol, setSymbol] = useState('BTCUSDT')
  const [tick, setTick] = useState<any>(null)
  const [signals, setSignals] = useState<any[]>([])
  const [status, setStatus] = useState<any>(null)
  const [err, setErr] = useState('')

  useEffect(() => {
    api.status().then(setStatus).catch((e) => setErr(String(e.message || e)))
  }, [])

  useEffect(() => {
    const stop = openTicks(symbol, setTick)
    api.signals(symbol).then((d) => setSignals(d.signals || [])).catch(() => {})
    const iv = setInterval(() => {
      api.signals(symbol).then((d) => setSignals(d.signals || [])).catch(() => {})
    }, 15000)
    return () => { stop(); clearInterval(iv) }
  }, [symbol])

  const mode = tick?.mode || status?.mode || 'paper'
  const consensus = tick?.consensus
  const portfolio = tick?.portfolio

  const body = useMemo(() => {
    const common = { symbol, setSymbol, tick, signals, consensus, portfolio, status, refreshStatus: () => api.status().then(setStatus) }
    switch (tab) {
      case 'markets': return <Markets {...common} />
      case 'chart': return <Chart {...common} />
      case 'order': return <OrderTicket {...common} />
      case 'bots': return <Bots {...common} />
      case 'signals': return <Signals {...common} />
      case 'portfolio': return <Portfolio {...common} />
      case 'settings': return <Settings {...common} />
    }
  }, [tab, symbol, tick, signals, consensus, portfolio, status])

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
              {symbol} · consensus {consensus?.score ?? '—'} · {consensus?.action ?? '—'}
            </div>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <span className={`pill ${mode === 'live' ? 'live' : 'paper'}`}>{mode.toUpperCase()}</span>
            <span className="pill">min $1</span>
            {portfolio?.killSwitch && <span className="pill live">KILL</span>}
          </div>
        </div>
        {err && <div className="toast">Engine: {err}（請先啟動 services/engine）</div>}
        {body}
      </div>
    </div>
  )
}
