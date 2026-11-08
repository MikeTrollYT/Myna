export function Bird({ className = '' }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 512 512"
      className={`bird ${className}`}
      aria-label="Logo de Myna STT"
      role="img"
    >
      <g className="legs">
        <rect fill="#f2b705" x="248" y="382" width="16" height="68" rx="8" />
        <rect fill="#f2b705" x="216" y="422" width="16" height="28" rx="8" />
        <rect fill="#f2b705" x="280" y="422" width="16" height="28" rx="8" />
      </g>
      <g className="body">
        <rect fill="#6b4a3b" x="376" y="170" width="16" height="136" rx="8" />
        <rect fill="#6b4a3b" x="344" y="182" width="16" height="150" rx="8" />
        <rect fill="#6b4a3b" x="312" y="266" width="16" height="80" rx="8" />
        <rect fill="#6b4a3b" x="280" y="294" width="16" height="64" rx="8" />
        <rect fill="#6b4a3b" x="248" y="318" width="16" height="48" rx="8" />
        <rect fill="#6b4a3b" x="216" y="342" width="16" height="16" rx="8" />
        <rect fill="#1c1e26" x="312" y="170" width="16" height="80" rx="8" />
        <rect fill="#1c1e26" x="280" y="190" width="16" height="88" rx="8" />
        <rect fill="#1c1e26" x="248" y="210" width="16" height="92" rx="8" />
        <rect fill="#1c1e26" x="216" y="230" width="16" height="96" rx="8" />
        <rect fill="#1c1e26" x="184" y="250" width="16" height="90" rx="8" />
        <rect fill="#1c1e26" x="152" y="270" width="16" height="76" rx="8" />
        <rect fill="#1c1e26" x="120" y="290" width="16" height="66" rx="8" />
        <rect fill="#1c1e26" x="88" y="310" width="16" height="56" rx="8" />
        <rect fill="#1c1e26" x="56" y="330" width="16" height="46" rx="8" />
        <rect fill="#1c1e26" x="24" y="350" width="16" height="36" rx="8" />
        <g className="head">
          <rect fill="#f2b705" x="408" y="80" width="16" height="44" rx="8" />
          <rect fill="#f2b705" x="440" y="90" width="16" height="30" rx="8" />
          <rect fill="#f2b705" x="472" y="100" width="16" height="16" rx="8" />
          <rect fill="#1c1e26" x="312" y="74" width="16" height="80" rx="8" />
          <rect fill="#1c1e26" x="344" y="62" width="16" height="104" rx="8" />
          <rect fill="#1c1e26" x="376" y="74" width="16" height="80" rx="8" />
        </g>
      </g>
    </svg>
  )
}
