import { useEffect, useState } from 'react'
import FinnAvatar from './FinnAvatar'

const FEATURES = [
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" />
      </svg>
    ),
    label: 'Sleep',
    desc: 'Better rest, sleep hygiene tips, and understanding your sleep cycles.',
  },
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
      </svg>
    ),
    label: 'Nutrition',
    desc: 'Balanced eating, energy foods, hydration goals, and daily habits.',
  },
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
      </svg>
    ),
    label: 'Mental Wellness',
    desc: 'Managing anxiety, stress, mood support, and mindfulness practices.',
  },
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <circle cx="12" cy="12" r="10" />
        <path d="M8 14s1.5 2 4 2 4-2 4-2" />
        <line x1="9" y1="9" x2="9.01" y2="9" strokeWidth="2" />
        <line x1="15" y1="9" x2="15.01" y2="9" strokeWidth="2" />
      </svg>
    ),
    label: 'Exercise',
    desc: 'Movement routines, recovery advice, and staying active every day.',
  },
]

const EXAMPLE_PROMPTS = [
  'How much water should I drink daily?',
  'Tips for better sleep tonight?',
  'I feel anxious — what can help?',
  'Best foods for sustained energy?',
]

export default function HomePage({ onStart }) {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    // Staggered entrance
    const t = setTimeout(() => setVisible(true), 50)
    return () => clearTimeout(t)
  }, [])

  function handlePrompt(text) {
    onStart(text)
  }

  return (
    <div
      className="min-h-screen w-full flex flex-col"
      style={{ background: 'var(--color-bg)' }}
    >
      {/* Nav bar */}
      <nav
        className="flex items-center justify-between px-6 py-4 border-b"
        style={{ borderColor: 'var(--color-border)', background: 'var(--color-surface)' }}
      >
        <div className="flex items-center gap-2.5">
          <FinnAvatar size={34} />
          <span
            className="text-lg font-semibold tracking-tight"
            style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text-primary)' }}
          >
            finn.ai
          </span>
        </div>
        <button
          onClick={() => onStart(null)}
          className="text-sm px-4 py-1.5 rounded-full cursor-pointer transition-all duration-200"
          style={{
            border: '1px solid var(--color-teal)',
            color: 'var(--color-teal)',
            background: 'transparent',
            fontFamily: 'var(--font-body)',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'var(--color-teal-muted)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'transparent'
          }}
        >
          Open chat
        </button>
      </nav>

      {/* Hero */}
      <main className="flex-1 flex flex-col items-center justify-center px-6 py-16 text-center">
        <div
          className="flex flex-col items-center gap-6 transition-all duration-700"
          style={{
            opacity: visible ? 1 : 0,
            transform: visible ? 'translateY(0)' : 'translateY(16px)',
          }}
        >
          {/* Avatar + glow */}
          <div className="relative">
            <div
              className="absolute inset-0 rounded-full blur-2xl"
              style={{ background: 'rgba(61,214,200,0.15)', transform: 'scale(1.4)' }}
              aria-hidden="true"
            />
            <FinnAvatar size={80} />
          </div>

          <div className="flex flex-col gap-2 max-w-md">
            <h1
              className="text-4xl sm:text-5xl font-semibold leading-tight"
              style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-text-primary)' }}
            >
              Meet Finn
            </h1>
            <p
              className="text-lg font-light"
              style={{ color: 'var(--color-text-muted)' }}
            >
              Your personal wellness companion — powered by a curated health knowledge base.
            </p>
          </div>

          {/* CTA */}
          <button
            onClick={() => onStart(null)}
            className="mt-2 px-8 py-3.5 rounded-full text-base font-medium cursor-pointer transition-all duration-200"
            style={{
              background: 'var(--color-teal)',
              color: '#0d1117',
              fontFamily: 'var(--font-body)',
              boxShadow: '0 0 24px rgba(61,214,200,0.25)',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'var(--color-teal-dim)'
              e.currentTarget.style.boxShadow = '0 0 32px rgba(61,214,200,0.35)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'var(--color-teal)'
              e.currentTarget.style.boxShadow = '0 0 24px rgba(61,214,200,0.25)'
            }}
          >
            Start talking to Finn
          </button>
        </div>

        {/* Feature cards */}
        <div
          className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-14 w-full max-w-2xl transition-all duration-700 delay-150"
          style={{
            opacity: visible ? 1 : 0,
            transform: visible ? 'translateY(0)' : 'translateY(16px)',
          }}
        >
          {FEATURES.map(({ icon, label, desc }) => (
            <div
              key={label}
              className="flex flex-col gap-2 rounded-2xl p-4 text-left"
              style={{
                background: 'var(--color-surface)',
                border: '1px solid var(--color-border)',
              }}
            >
              <span style={{ color: 'var(--color-teal)' }}>{icon}</span>
              <span
                className="text-sm font-medium"
                style={{ color: 'var(--color-text-primary)' }}
              >
                {label}
              </span>
              <span
                className="text-xs leading-relaxed"
                style={{ color: 'var(--color-text-muted)' }}
              >
                {desc}
              </span>
            </div>
          ))}
        </div>

        {/* Example prompts */}
        <div
          className="mt-10 flex flex-col items-center gap-3 w-full max-w-lg transition-all duration-700 delay-300"
          style={{
            opacity: visible ? 1 : 0,
            transform: visible ? 'translateY(0)' : 'translateY(16px)',
          }}
        >
          <p className="text-xs uppercase tracking-widest" style={{ color: 'var(--color-text-subtle)' }}>
            Try asking
          </p>
          <div className="flex flex-wrap justify-center gap-2">
            {EXAMPLE_PROMPTS.map((prompt) => (
              <button
                key={prompt}
                onClick={() => handlePrompt(prompt)}
                className="text-sm px-3.5 py-1.5 rounded-full cursor-pointer transition-all duration-200"
                style={{
                  background: 'var(--color-surface)',
                  border: '1px solid var(--color-border)',
                  color: 'var(--color-text-muted)',
                  fontFamily: 'var(--font-body)',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = 'var(--color-teal)'
                  e.currentTarget.style.color = 'var(--color-teal)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = 'var(--color-border)'
                  e.currentTarget.style.color = 'var(--color-text-muted)'
                }}
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer
        className="text-center py-4 text-xs border-t"
        style={{ borderColor: 'var(--color-border)', color: 'var(--color-text-subtle)' }}
      >
        Finn is not a doctor. Always consult a healthcare professional for medical advice.
      </footer>
    </div>
  )
}
