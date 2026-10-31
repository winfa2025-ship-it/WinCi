import TimeframePicker, { type Timeframe } from '../components/TimeframePicker'

type Props = {
  symbol: string
  tick: any
  timeframe: string
  setTimeframe: (tf: Timeframe) => void
}

export default function Chart({ symbol, tick, timeframe, setTimeframe }: Props) {
  const price = tick?.price ?? 0
  const candles: any[] = tick?.candles?.length
    ? tick.candles
    : Array.from({ length: 40 }, (_, i) => {
        const y = 80 + Math.sin(i / 3 + (tick?.ts || 0) / 5) * 30 + (i % 5) * 2
        return { c: y, o: y, h: y + 5, l: y - 5 }
      })

  const closes = candles.map((c) => Number(c.c))
  const min = Math.min(...closes)
  const max = Math.max(...closes)
  const span = Math.max(max - min, 1e-9)
  const w = 400
  const h = 160
  const pts = closes
    .map((c, i) => {
      const x = (i / Math.max(closes.length - 1, 1)) * (w - 4) + 2
      const y = h - 8 - ((c - min) / span) * (h - 16)
      return `${x},${y}`
    })
    .join(' ')

  return (
    <div className="grid cols-2">
      <div className="card">
        <div className="card-head">
          <h2>Chart · {symbol} · {timeframe}</h2>
          <TimeframePicker value={timeframe} onChange={setTimeframe} label="K線" />
        </div>
        <div className="metric">{price || '—'}</div>
        <div className="chart-stub" style={{ marginTop: '0.75rem' }}>
          <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none">
            <polyline fill="none" stroke="#3dff9a" strokeWidth="2" points={pts} />
          </svg>
        </div>
        <p className="muted" style={{ marginTop: '0.75rem' }}>
          短炒時框 {timeframe}（{tick?.timeframeSec || '—'}s）· OHLC stub · v2 TradingView
        </p>
      </div>
      <div className="card">
        <h2>Consensus · {timeframe}</h2>
        <div className={`metric ${(tick?.consensus?.score || 0) >= 0 ? 'up' : 'down'}`}>
          {tick?.consensus?.score ?? '—'}
        </div>
        <p>action: <strong>{tick?.consensus?.action}</strong></p>
        <p className="muted">
          bull {tick?.consensus?.bullish} · bear {tick?.consensus?.bearish} · neut {tick?.consensus?.neutral}
          {tick?.consensus?.aiBoost ? ` · AI boost ${tick.consensus.aiBoost}` : ''}
        </p>
      </div>
    </div>
  )
}
