import { useEffect, useState } from 'react'
import { api } from '../lib/api'

type Props = { status: any; refreshStatus: () => void }

export default function Settings({ status, refreshStatus }: Props) {
  const [mode, setMode] = useState(status?.mode || 'paper')
  const [dsKey, setDsKey] = useState('')
  const [ds, setDs] = useState<any>(null)
  const [msg, setMsg] = useState('')

  useEffect(() => {
    setMode(status?.mode || 'paper')
    api.deepseekStatus().then(setDs).catch(() => {})
  }, [status])

  async function saveMode() {
    try {
      await api.setMode(mode)
      refreshStatus()
      setMsg(`Mode → ${mode}`)
    } catch (e: any) {
      setMsg(String(e.message || e))
    }
  }

  async function saveDeepseek() {
    try {
      const r = await api.setDeepseekKey(dsKey)
      setDs(await api.deepseekStatus())
      setDsKey('')
      setMsg(r.configured ? 'DeepSeek key saved (session)' : 'DeepSeek key cleared')
      refreshStatus()
    } catch (e: any) {
      setMsg(String(e.message || e))
    }
  }

  return (
    <div className="grid cols-2">
      <div className="card">
        <h2>Trading mode</h2>
        <label className="field">Mode
          <select value={mode} onChange={(e) => setMode(e.target.value)}>
            <option value="paper">paper（預設）</option>
            <option value="live">live（需幣安 key；v0.1 stub）</option>
          </select>
        </label>
        <button className="primary" style={{ marginTop: '0.75rem' }} onClick={saveMode}>Apply</button>
        <p className="muted" style={{ marginTop: '0.75rem' }}>
          Binance configured: {String(status?.binance?.configured)} · {status?.binance?.note}
        </p>
        <p className="muted">Risk: min ${status?.minNotionalUsd} · max pos ${status?.maxPositionUsd} · daily loss ${status?.dailyLossLimitUsd}</p>
      </div>
      <div className="card">
        <h2>DeepSeek AI</h2>
        <p className="muted">Base URL: https://api.deepseek.com · 紙上模式可不填</p>
        <p>Configured: <strong>{String(ds?.configured ?? status?.deepseek?.configured)}</strong></p>
        <label className="field">DEEPSEEK_API_KEY（session；建議用 .env）
          <input type="password" value={dsKey} placeholder="sk-…" onChange={(e) => setDsKey(e.target.value)} autoComplete="off" />
        </label>
        <div className="row-form" style={{ marginTop: '0.75rem' }}>
          <button className="primary" onClick={saveDeepseek}>Save key</button>
          <button onClick={() => { setDsKey(''); api.setDeepseekKey('').then(() => api.deepseekStatus().then(setDs)) }}>Clear</button>
        </div>
        {msg && <div className="toast">{msg}</div>}
      </div>
    </div>
  )
}
