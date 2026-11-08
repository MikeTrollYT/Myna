const HEIGHTS = [0.4, 0.7, 1, 0.55, 0.85, 0.35, 0.9, 0.6, 1, 0.45, 0.75, 0.5, 0.95, 0.4, 0.65, 0.8, 0.3, 0.7]

export function Waveform({
  color = 'bg-ink',
  count = HEIGHTS.length,
  active = true,
  className = '',
}: {
  color?: string
  count?: number
  active?: boolean
  className?: string
}) {
  return (
    <div className={`flex h-10 shrink-0 items-center gap-[3px] ${className}`} aria-hidden="true">
      {HEIGHTS.slice(0, count).map((h, i) => (
        <span
          key={i}
          className={`wave-bar block w-[3px] rounded-full transition-opacity duration-300 ${color} ${active ? '' : 'opacity-30'}`}
          style={{
            height: `${active ? h * 100 : 18}%`,
            animationDelay: `${(i * 97) % 1200}ms`,
            animationPlayState: active ? 'running' : 'paused',
            transition: 'height 300ms ease, opacity 300ms ease',
          }}
        />
      ))}
    </div>
  )
}
