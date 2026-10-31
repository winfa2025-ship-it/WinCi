type Props = { symbol: string; tick: any }

export default function Chart({ symbol, tick }: Props) {
  const price = tick?.price ?? 0
  const pts = Array.from({ length: 40 }, (_, i) => {
    const y = 80 + Math.sin(i / 3 + (tick?.ts || 0) / 5) * 30 + (i % 5) * 2
    return `${i * 10},${y}`
  }).join(' ')
  return (
    <div className="grid cols-2">
      <div className="card">
        <h2>Chart · {symbol}</h2>
        <div className="metric">{price || '—'}</div>
        <div className="chart-stub" style={{ marginTop: '0.75rem' }}>
          <svg viewBox="0 0 400 160" preserveAspectRatio="none">
            <polyline fill="none" stroke="#3dff9a" strokeWidth="2" points={pts} />
          </svg>
        </div>
        <p className="muted" style={{ marginTop: '0.75rem' }}>MVP sparkline stub · v2 TradingView</p>
      </div>
      <div className="card">
        <h2>Consensus</h2>
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
