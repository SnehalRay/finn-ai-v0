export default function FinnAvatar({ size = 32 }) {
  return (
    <div
      className="flex items-center justify-center rounded-full flex-shrink-0"
      style={{
        width: size,
        height: size,
        background: 'var(--color-teal-muted)',
        border: '1px solid rgba(61,214,200,0.25)',
      }}
      aria-hidden="true"
    >
      <svg width={size * 0.6} height={size * 0.6} viewBox="0 0 28 28" fill="none">
        <circle cx="14" cy="14" r="13" stroke="var(--color-teal)" strokeWidth="1.5" />
        <path d="M8 14c0-3.314 2.686-6 6-6s6 2.686 6 6" stroke="var(--color-teal)" strokeWidth="1.5" strokeLinecap="round" />
        <circle cx="10.5" cy="15.5" r="1.5" fill="var(--color-teal)" />
        <circle cx="17.5" cy="15.5" r="1.5" fill="var(--color-teal)" />
        <path d="M10.5 19.5c1 1 6 1 7 0" stroke="var(--color-teal)" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
    </div>
  )
}
