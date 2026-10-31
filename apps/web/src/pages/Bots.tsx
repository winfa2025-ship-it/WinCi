import { useEffect, useState } from 'react'
import { api } from '../lib/api'

type Props = { tick: any }

const DISCLAIMER = '唔保證盈利／過去表現唔代表將來'

export default function Bots({ tick }: Props) {
  const [bot, setBot] = useState<any>(tick?.bot)
  const [auto, setAuto] = useState<any>(tick?.autoearn)
  const [msg, setMsg] = useState('')
  const [posSize, setPosSize] = useState('25')
  const [maxLoss, setMaxLoss] = useState('5')

  useEffect(() => {
    setBot(tick?.bot)
    setAuto(tick?.autoearn)
    if (tick?.autoearn?.order_notional_usd != null) setPosSize(String(tick.autoearn.order_notional_usd))
    if (tick?.autoearn?.max_daily_loss_pct != null) setMaxLoss(String(tick.autoearn.max_daily_loss_pct))
  }, [tick?.bot, tick?.autoearn])

  async function toggleMomentum() {
    if (!bot) return
    const next = await api.patchBot(bot.id, { enabled: !bot.enabled })
    setBot(next)
    setMsg(next.enabled ? 'Momentum running' : 'Momentum stopped')
  }

  async function saveNotional(v: string) {
    if (!bot) return
    const next = await api.patchBot(bot.id, { order_notional_usd: Number(v) })
    setBot(next)
  }

  async function toggleAutoEarn() {
    if (!auto) return
    if (!auto.enabled) {
      const ok = window.confirm(
        `開啟 AutoEarn？\n\n${DISCLAIMER}\n\n預設紙上模式；真錢風險自負。`,
      )
      if (!ok) return
    }
    const next = await api.patchBot(auto.id, { enabled: !auto.enabled })
    setAuto(next)
    setMsg(next.enabled ? 'AutoEarn 已開（紙上／有風險上限）' : 'AutoEarn 已停')
  }

  async function saveAuto() {
    if (!auto) return
    const next = await api.patchBot(auto.id, {
      position_size_usd: Number(posSize),
      max_daily_loss_pct: Number(maxLoss),
    })
    setAuto(next)
    setMsg('AutoEarn 參數已存')
  }

  async function killAuto() {
    if (!auto) return
    const next = await api.patchBot(auto.id, { kill_switch: true, enabled: false })
    setAuto(next)
    setMsg('AutoEarn kill switch ON')
  }

  async function resetKill() {
    const r = await api.resetKill()
    setAuto(r.autoearn)
    setMsg('Kill switches reset')
  }

  return (
    <div className="grid cols-2">
      <div className="card">
        <h2>Momentum bot</h2>
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
              <button className={bot.enabled ? 'danger' : 'primary'} onClick={toggleMomentum}>
                {bot.enabled ? 'Stop' : 'Start'}
              </button>
            </div>
            {bot.last_error && <div className="toast">{bot.last_error}</div>}
          </>
        )}
      </div>

      <div className="card">
        <h2>AutoEarn（自動幫你做單）</h2>
        <div className="disclaimer">{DISCLAIMER}</div>
        <p className="muted" style={{ marginTop: '0.5rem' }}>
          Opt-in 機械人（延伸 momentum）。預設紙上；有倉位美金、日虧 %、kill switch。
          <strong> 唔保證賺錢。</strong>
        </p>
        {!auto ? <p className="muted">Loading…</p> : (
          <>
            <div className="grid cols-3" style={{ marginTop: '0.75rem' }}>
              <div><div className="muted">Status</div><div>{auto.enabled ? 'ON' : 'OFF'}{auto.kill_switch ? ' · KILL' : ''}</div></div>
              <div><div className="muted">Last</div><div>{auto.last_action}</div></div>
              <div><div className="muted">Symbol</div><div>{auto.symbol}</div></div>
            </div>
            <div className="row-form" style={{ marginTop: '0.75rem' }}>
              <label className="field">Position size USD
                <input value={posSize} onChange={(e) => setPosSize(e.target.value)} />
              </label>
              <label className="field">Max daily loss %
                <input value={maxLoss} onChange={(e) => setMaxLoss(e.target.value)} />
              </label>
              <button onClick={saveAuto}>Save</button>
            </div>
            <div className="row-form" style={{ marginTop: '0.75rem' }}>
              <button className={auto.enabled ? 'danger' : 'primary'} onClick={toggleAutoEarn}>
                {auto.enabled ? 'Stop AutoEarn' : 'Start AutoEarn'}
              </button>
              <button className="danger" onClick={killAuto}>Kill switch</button>
              <button onClick={resetKill}>Reset kills</button>
            </div>
            {auto.last_error && <div className="toast">{auto.last_error}</div>}
          </>
        )}
        {msg && <div className="toast">{msg}</div>}
      </div>
    </div>
  )
}
