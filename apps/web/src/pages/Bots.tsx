import { useEffect, useState } from 'react'
import { api } from '../lib/api'

type Props = { tick: any }

export default function Bots({ tick }: Props) {
  const [bot, setBot] = useState<any>(tick?.bot)
  const [msg, setMsg] = useState('')

  useEffect(() => { setBot(tick?.bot) }, [tick?.bot])

  async function toggle() {
    if (!bot) return
    const next = await api.patchBot(bot.id, { enabled: !bot.enabled })
    setBot(next)
    setMsg(next.enabled ? 'Bot running' : 'Bot stopped')
  }

  async function saveNotional(v: string) {
    if (!bot) return
    const next = await api.patchBot(bot.id, { order_notional_usd: Number(v) })
    setBot(next)
  }

  return (
    <div className="card">
      <h2>Bots</h2>
      {!bot ? <p className="muted">Loading…</p> : (
        <>
          <div className="grid cols-3">
            <div><div className="muted">Name</div><div className="metric" style={{ fontSize: '1.1rem' }}>{bot.name}</div></div>
            <div><div className="muted">Symbol</div><div>{bot.symbol}</div></div>
            <div><div className="muted">Last</div><div>{bot.last_action}</div></div>
          </div>
          <p className="muted">buy ≥ {bot.buy_threshold} · sell ≤ {bot.sell_threshold} · cooldown {bot.cooldown_sec}s</p>
          <div className="row-form" style={{ marginTop: '0.75rem' }}>
            <label className="field">Order notional USD
              <input defaultValue={bot.order_notional_usd} onBlur={(e) => saveNotional(e.target.value)} />
            </label>
            <button className={bot.enabled ? 'danger' : 'primary'} onClick={toggle}>
              {bot.enabled ? 'Stop' : 'Start'}
            </button>
          </div>
          {bot.last_error && <div className="toast">{bot.last_error}</div>}
          {msg && <div className="toast">{msg}</div>}
        </>
      )}
    </div>
  )
}
