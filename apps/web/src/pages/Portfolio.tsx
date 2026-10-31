import { useEffect, useState } from 'react'
import { api } from '../lib/api'

type Props = { portfolio: any }

export default function Portfolio({ portfolio }: Props) {
  const [orders, setOrders] = useState<any>({ orders: [], fills: [] })
  useEffect(() => {
    api.orders().then(setOrders).catch(() => {})
    const iv = setInterval(() => api.orders().then(setOrders).catch(() => {}), 5000)
    return () => clearInterval(iv)
  }, [portfolio?.usdt])

  return (
    <div className="grid cols-2">
      <div className="card">
        <h2>Portfolio</h2>
        <div className="metric">${portfolio?.equity ?? '—'}</div>
        <p className="muted">USDT {portfolio?.usdt} · realized today {portfolio?.realizedPnlToday}</p>
        {portfolio?.killSwitch && (
          <div className="toast">Kill-switch: {portfolio.killReason}
            <button style={{ marginLeft: 8 }} onClick={() => api.resetKill()}>Reset</button>
          </div>
        )}
        <table>
          <thead><tr><th>Symbol</th><th>Qty</th><th>Notional</th><th>uPnL</th></tr></thead>
          <tbody>
            {(portfolio?.positions || []).map((p: any) => (
              <tr key={p.symbol}>
                <td>{p.symbol}</td><td>{p.quantity}</td><td>{p.notional}</td>
                <td className={p.unrealizedPnl >= 0 ? 'up' : 'down'}>{p.unrealizedPnl}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="card">
        <h2>Recent fills</h2>
        <table>
          <thead><tr><th>Side</th><th>Symbol</th><th>Qty</th><th>Price</th><th>Notional</th></tr></thead>
          <tbody>
            {(orders.fills || []).slice(0, 20).map((f: any, i: number) => (
              <tr key={i}>
                <td className={f.side === 'buy' ? 'up' : 'down'}>{f.side}</td>
                <td>{f.symbol}</td><td>{f.quantity}</td><td>{f.price}</td><td>{f.notional}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
