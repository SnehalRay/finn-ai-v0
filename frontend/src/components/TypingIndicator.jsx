import FinnAvatar from './FinnAvatar'

export default function TypingIndicator() {
  return (
    <div className="flex items-end gap-2 max-w-xs" role="status" aria-label="Finn is typing">
      <FinnAvatar size={32} />
      <div
        className="flex items-center gap-1 px-4 py-3 rounded-2xl rounded-bl-sm"
        style={{ background: 'var(--color-finn-bubble)', border: '1px solid var(--color-border)' }}
      >
        {[0, 150, 300].map((delay) => (
          <span
            key={delay}
            className="block w-2 h-2 rounded-full"
            style={{
              background: 'var(--color-text-muted)',
              animation: `typing-dot 1.2s ease-in-out ${delay}ms infinite`,
            }}
          />
        ))}
      </div>
      <style>{`
        @keyframes typing-dot {
          0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
          30% { transform: translateY(-4px); opacity: 1; }
        }
      `}</style>
    </div>
  )
}
