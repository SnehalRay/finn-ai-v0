import { useState, useEffect, useRef, useCallback } from 'react'
import HomePage from './components/HomePage'
import Header from './components/Header'
import MessageBubble from './components/MessageBubble'
import TypingIndicator from './components/TypingIndicator'
import ChatInput from './components/ChatInput'
import { sendMessage, checkHealth } from './api'

const WELCOME = {
  id: 'welcome',
  role: 'assistant',
  content: "Hi! I'm Finn, your personal wellness companion. I'm here to help with questions about sleep, nutrition, hydration, exercise, and mental wellness.\n\nHow are you feeling today?",
  blocked: false,
  blockReason: null,
  sourcesUsed: false,
}

function ChatView({ online, initialPrompt, onBack }) {
  const [messages, setMessages] = useState([WELCOME])
  const [input, setInput] = useState(initialPrompt ?? '')
  const [isTyping, setIsTyping] = useState(false)
  const bottomRef = useRef(null)

  // Auto-send if the user clicked an example prompt on the home page
  const didAutoSend = useRef(false)
  useEffect(() => {
    if (initialPrompt && !didAutoSend.current) {
      didAutoSend.current = true
      handleSend(initialPrompt)
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  const handleSend = useCallback(async (overrideText) => {
    const text = (overrideText ?? input).trim()
    if (!text || isTyping) return

    setMessages((prev) => [...prev, { id: Date.now(), role: 'user', content: text }])
    setInput('')
    setIsTyping(true)

    try {
      const data = await sendMessage(text)
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          role: 'assistant',
          content: data.message,
          blocked: data.blocked,
          blockReason: data.block_reason,
          sourcesUsed: data.sources_used,
        },
      ])
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          role: 'assistant',
          content: "I'm having a little trouble connecting right now. Please check that the backend is running and try again.",
          blocked: false,
          blockReason: null,
          sourcesUsed: false,
        },
      ])
    } finally {
      setIsTyping(false)
    }
  }, [input, isTyping])

  return (
    <div
      className="flex flex-col h-screen"
      style={{ background: 'var(--color-bg)', maxWidth: '768px', margin: '0 auto', width: '100%' }}
    >
      <Header online={online === true} onBack={onBack} />

      <main
        className="flex-1 overflow-y-auto px-4 sm:px-6 py-6 flex flex-col gap-4"
        role="log"
        aria-live="polite"
        aria-label="Conversation with Finn"
      >
        {messages.map((msg) => (
          <MessageBubble
            key={msg.id}
            role={msg.role}
            content={msg.content}
            blocked={msg.blocked}
            blockReason={msg.blockReason}
            sourcesUsed={msg.sourcesUsed}
          />
        ))}

        {isTyping && <TypingIndicator />}
        <div ref={bottomRef} aria-hidden="true" />
      </main>

      <ChatInput
        value={input}
        onChange={setInput}
        onSubmit={() => handleSend()}
        disabled={isTyping}
      />
    </div>
  )
}

export default function App() {
  const [page, setPage] = useState('home') // 'home' | 'chat'
  const [initialPrompt, setInitialPrompt] = useState(null)
  const [online, setOnline] = useState(null)

  useEffect(() => {
    checkHealth().then(setOnline)
  }, [])

  function enterChat(prompt) {
    setInitialPrompt(prompt ?? null)
    setPage('chat')
  }

  // Slide transition
  return (
    <div style={{ height: '100%', overflow: 'hidden', position: 'relative' }}>
      {/* Home page */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transition: 'transform 0.4s cubic-bezier(0.4,0,0.2,1), opacity 0.4s ease',
          transform: page === 'home' ? 'translateX(0)' : 'translateX(-100%)',
          opacity: page === 'home' ? 1 : 0,
          pointerEvents: page === 'home' ? 'auto' : 'none',
          overflowY: 'auto',
        }}
      >
        <HomePage onStart={enterChat} />
      </div>

      {/* Chat page */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transition: 'transform 0.4s cubic-bezier(0.4,0,0.2,1), opacity 0.4s ease',
          transform: page === 'chat' ? 'translateX(0)' : 'translateX(100%)',
          opacity: page === 'chat' ? 1 : 0,
          pointerEvents: page === 'chat' ? 'auto' : 'none',
        }}
      >
        {page === 'chat' && (
          <ChatView online={online} initialPrompt={initialPrompt} onBack={() => setPage('home')} />
        )}
      </div>
    </div>
  )
}
