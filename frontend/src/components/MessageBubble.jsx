import FinnAvatar from './FinnAvatar'

function SourcesBadge() {
  return (
    <span
      className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full mt-1"
      style={{
        background: 'var(--color-teal-muted)',
        color: 'var(--color-teal)',
        border: '1px solid rgba(61,214,200,0.2)',
      }}
      title="Answer grounded in Finn's knowledge base"
    >
      <svg width="10" height="10" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
        <path d="M2 2h5v2H4v8h8v-3h2v5H2V2zm9 0h3v3h-2V3.414L7.707 8.707 6.293 7.293 11.586 2H11V2z" />
      </svg>
      backed by knowledge base
    </span>
  )
}

function BlockedBadge({ reason }) {
  const labels = {
    CRISIS: 'Crisis support',
    MEDICAL: 'Medical boundary',
    OTHER: 'Out of scope',
  }
  return (
    <span
      className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full mt-1"
      style={{
        background: 'rgba(245,158,11,0.12)',
        color: '#f59e0b',
        border: '1px solid rgba(245,158,11,0.3)',
      }}
    >
      <svg width="10" height="10" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
        <path d="M8 1a7 7 0 1 0 0 14A7 7 0 0 0 8 1zm.75 3.5v4h-1.5v-4h1.5zm0 5.5v1.5h-1.5V10h1.5z" />
      </svg>
      {labels[reason] ?? 'Guided response'}
    </span>
  )
}

export default function MessageBubble({ role, content, blocked, blockReason, sourcesUsed }) {
  const isUser = role === 'user'

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div
          className="max-w-[75%] sm:max-w-md px-4 py-3 rounded-2xl rounded-br-sm text-sm"
          style={{
            background: 'var(--color-user-bubble)',
            border: '1px solid var(--color-user-bubble-border)',
            color: 'var(--color-text-primary)',
          }}
        >
          {content}
        </div>
      </div>
    )
  }

  return (
    <div className="flex items-end gap-2">
      <FinnAvatar size={32} />
      <div className="max-w-[75%] sm:max-w-md flex flex-col items-start">
        <div
          className="px-4 py-3 rounded-2xl rounded-bl-sm text-sm leading-relaxed"
          style={{
            background: blocked ? 'var(--color-amber-bg)' : 'var(--color-finn-bubble)',
            border: blocked
              ? '1px solid var(--color-amber-border)'
              : '1px solid var(--color-border)',
            color: 'var(--color-text-primary)',
            whiteSpace: 'pre-wrap',
          }}
        >
          {content}
        </div>
        <div className="flex flex-wrap gap-1 mt-1 pl-1">
          {sourcesUsed && !blocked && <SourcesBadge />}
          {blocked && <BlockedBadge reason={blockReason} />}
        </div>
      </div>
    </div>
  )
}
