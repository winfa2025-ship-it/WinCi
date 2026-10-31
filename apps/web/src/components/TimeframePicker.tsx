export const TIMEFRAMES = ['1m', '5m', '15m'] as const
export type Timeframe = (typeof TIMEFRAMES)[number]

type Props = {
  value: string
  onChange: (tf: Timeframe) => void
  size?: 'sm' | 'md'
  label?: string
}

/** Short-trade TF selector: 1m / 5m / 15m */
export default function TimeframePicker({ value, onChange, size = 'md', label }: Props) {
  return (
    <div className={`tf-picker ${size}`} role="group" aria-label={label || 'Timeframe'}>
      {label && <span className="tf-label">{label}</span>}
      <div className="tf-btns">
        {TIMEFRAMES.map((tf) => (
          <button
            key={tf}
            type="button"
            className={value === tf ? 'active' : ''}
            onClick={() => onChange(tf)}
          >
            {tf}
          </button>
        ))}
      </div>
    </div>
  )
}
