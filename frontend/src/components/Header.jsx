import FinnAvatar from './FinnAvatar'

export default function Header({ online, onBack }) {
  return (
    <header
      className="flex-shrink-0 flex items-center justify-between px-4 sm:px-6 py-3 border-b"
      style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}
    >
      <div className="flex items-center gap-3">
        {onBack && (
          <button
            onClick={onBack}
            className="flex items-center justify-center w-8 h-8 rounded-full cursor-pointer transition-all duration-200"
            style={{ color: 'var(--color-text-muted)', background: 'transparent', border: '1px solid var(--color-border)' }}
            onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--color-teal)'; e.currentTarget.style.borderColor = 'var(--color-teal)' }}
            onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--color-text-muted)'; e.currentTarget.style.borderColor = 'var(--color-border)' }}
            aria-label="Back to home"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <polyline points="15 18 9 12 15 6" />
            </svg>
          </button>
        )}
        <FinnAvatar size={40} />
        <div className="flex flex-col">
          <span
            className="font-semibold text-base leading-tight"
            style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text-primary)' }}
          >
            Finn
          </span>
          <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
            Your personal wellness companion
          </span>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <span
          className="w-2 h-2 rounded-full"
          style={{ background: online ? '#3dd6c8' : '#6e7681' }}
          aria-hidden="true"
        />
        <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
          {online ? 'Online' : 'Offline'}
        </span>
      </div>
    </header>
  )
}
