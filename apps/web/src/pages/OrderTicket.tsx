import { useState } from 'react'
import { api } from '../lib/api'

type Props = { symbol: string; setSymbol: (s: string) => void; tick: any; status: any }

export default function OrderTicket({ symbol, setSymbol, tick, status }: Props) {
  const [side, setSide] = useState<'buy' | 'sell'>('buy')
  const [qty, setQty] = useState('0.001')
  const [price, setPrice] = useState('')
  const [type, setType] = useState<'market' | 'limit'>('market')
  const [msg, setMsg] = useState('')
  const px = tick?.price

  async function submit() {
    setMsg('')
    try {
      const body: any = { symbol, side, quantity: Number(qty), type }
      if (type === 'limit' && price) body.price = Number(price)
      const r = await api.order(body)
      setMsg(`Filled #${r.order?.id} @ ${r.order?.price} · notional $${r.order?.notional}`)
    } catch (e: any) {
      setMsg(String(e.message || e))
    }
  }

  return (
    <div className="card">
      <h2>Order ticket</h2>
      <div className="row-form">
        <label className="field">Symbol
          <select value={symbol} onChange={(e) => setSymbol(e.target.value)}>
            {(status?.symbols || ['BTCUSDT']).map((s: string) => <option key={s}>{s}</option>)}
          </select>
        </label>
        <label className="field">Side
          <select value={side} onChange={(e) => setSide(e.target.value as any)}>
            <option value="buy">Buy</option>
            <option value="sell">Sell</option>
          </select>
        </label>
        <label className="field">Type
          <select value={type} onChange={(e) => setType(e.target.value as any)}>
            <option value="market">Market</option>
            <option value="limit">Limit</option>
          </select>
        </label>
        <label className="field">Qty
          <input value={qty} onChange={(e) => setQty(e.target.value)} />
        </label>
        {type === 'limit' && (
          <label className="field">Price
            <input value={price} placeholder={String(px || '')} onChange={(e) => setPrice(e.target.value)} />
          </label>
        )}
        <button className={side === 'buy' ? 'primary' : 'danger'} onClick={submit}>
          {side === 'buy' ? 'Buy' : 'Sell'}
        </button>
      </div>
      <p className="muted">Mark {px ?? '—'} · min notional ${status?.minNotionalUsd ?? 1}</p>
      {msg && <div className="toast">{msg}</div>}
    </div>
  )
}
