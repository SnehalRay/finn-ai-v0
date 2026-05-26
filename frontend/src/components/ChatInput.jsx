import { useRef, useEffect } from 'react'

export default function ChatInput({ value, onChange, onSubmit, disabled }) {
  const textareaRef = useRef(null)

  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 160) + 'px'
  }, [value])

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (!disabled && value.trim()) onSubmit()
    }
  }

  const charsLeft = 2000 - value.length
  const isNearLimit = charsLeft <= 200

  return (
    <div
      className="flex-shrink-0 border-t px-3 sm:px-6 py-3"
      style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}
    >
      <form
        onSubmit={(e) => { e.preventDefault(); if (!disabled && value.trim()) onSubmit() }}
        className="flex items-end gap-2"
      >
        <div
          className="flex-1 flex items-end rounded-2xl px-4 py-2 gap-2 transition-all duration-200"
          style={{
            background: 'var(--color-surface-elevated)',
            border: '1px solid var(--color-border)',
          }}
        >
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about sleep, nutrition, mental wellness…"
            maxLength={2000}
            rows={1}
            disabled={disabled}
            className="flex-1 resize-none bg-transparent outline-none text-sm py-1 leading-relaxed"
            style={{
              color: 'var(--color-text-primary)',
              fontFamily: 'var(--font-body)',
              caretColor: 'var(--color-teal)',
            }}
            aria-label="Message to Finn"
          />
        </div>

        <button
          type="submit"
          disabled={disabled || !value.trim()}
          className="flex-shrink-0 w-10 h-10 flex items-center justify-center rounded-full transition-all duration-200 cursor-pointer"
          style={{
            background:
              disabled || !value.trim()
                ? 'var(--color-surface-elevated)'
                : 'var(--color-teal)',
            color:
              disabled || !value.trim()
                ? 'var(--color-text-subtle)'
                : '#0d1117',
            border: '1px solid var(--color-border)',
          }}
          aria-label="Send message"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </form>

      <div className="flex justify-between items-center mt-1.5 px-1">
        <span className="text-xs" style={{ color: 'var(--color-text-subtle)' }}>
          Finn is not a doctor — consult a healthcare professional for medical advice.
        </span>
        {isNearLimit && (
          <span
            className="text-xs ml-3 flex-shrink-0"
            style={{ color: charsLeft <= 50 ? '#f59e0b' : 'var(--color-text-subtle)' }}
            aria-live="polite"
          >
            {charsLeft}
          </span>
        )}
      </div>
    </div>
  )
}
