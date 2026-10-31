import { useState } from 'react'
import { api } from '../lib/api'
import TimeframePicker, { type Timeframe } from '../components/TimeframePicker'

type Props = {
  symbol: string
  signals: any[]
  consensus: any
  timeframe: string
  setTimeframe: (tf: Timeframe) => void
}

export default function Signals({ symbol, signals, consensus, timeframe, setTimeframe }: Props) {
  const [commentary, setCommentary] = useState('')
  const [busy, setBusy] = useState(false)

  async function askAi(boost: boolean) {
    setBusy(true)
    try {
      const r = await api.commentary(symbol, boost)
      setCommentary(r.commentary?.content || JSON.stringify(r))
    } catch (e: any) {
      setCommentary(String(e.message || e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="grid">
      <div className="card">
        <div className="card-head">
          <h2>100 Signal board · {symbol} · {timeframe}</h2>
          <TimeframePicker value={timeframe} onChange={setTimeframe} label="短炒" />
        </div>
        <p>
          Consensus <strong className={(consensus?.score || 0) >= 0 ? 'up' : 'down'}>{consensus?.score ?? '—'}</strong>
          {' '}→ {consensus?.action}
          {consensus?.aiBoost ? ` (AI boost ${consensus.aiBoost})` : ''}
        </p>
        <p className="muted">信號節奏跟住 {timeframe} K 線 bucket（唔係每秒亂跳）。</p>
        <div className="row-form" style={{ marginBottom: '0.75rem' }}>
          <button className="primary" disabled={busy} onClick={() => askAi(false)}>DeepSeek 短評</button>
          <button disabled={busy} onClick={() => askAi(true)}>短評 + AI boost</button>
        </div>
        {commentary && <pre style={{ whiteSpace: 'pre-wrap', background: '#0a0e13', padding: '0.75rem', borderRadius: 8 }}>{commentary}</pre>}
      </div>
      <div className="card">
        <h3>{signals.length || 100} analyzers · {timeframe}</h3>
        <div className="signal-board">
          {(signals.length ? signals : Array.from({ length: 100 }, (_, i) => ({ id: i + 1, name: `Slot_${i + 1}`, score: 0, category: '—' }))).map((s) => (
            <div className="sig" key={s.id}>
              <div className="name" title={s.name}>#{s.id} {s.name}</div>
              <div className={s.score >= 0 ? 'up' : 'down'}>{s.score}</div>
              <div className="muted">{s.category}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
