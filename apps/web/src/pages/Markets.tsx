type Props = { symbol: string; setSymbol: (s: string) => void; tick: any }

export default function Markets({ symbol, setSymbol, tick }: Props) {
  const markets = tick?.markets || []
  return (
    <div className="card">
      <h2>Markets</h2>
      <table>
        <thead>
          <tr><th>Symbol</th><th>Price</th><th>Δ proxy</th><th></th></tr>
        </thead>
        <tbody>
          {markets.map((m: any) => (
            <tr key={m.symbol} style={{ background: m.symbol === symbol ? '#1a2436' : undefined }}>
              <td>{m.symbol}</td>
              <td>{m.price}</td>
              <td className={m.change24h >= 0 ? 'up' : 'down'}>{m.change24h}%</td>
              <td><button onClick={() => setSymbol(m.symbol)}>Select</button></td>
            </tr>
          ))}
        </tbody>
      </table>
      {!markets.length && <p className="muted">Waiting for SSE ticks…</p>}
    </div>
  )
}
