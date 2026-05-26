const BASE = '/chat'

let sessionId = null

export function getSessionId() {
  return sessionId
}

export async function sendMessage(message) {
  const body = {
    user_id: 'web-user',
    message,
    ...(sessionId ? { session_id: sessionId } : {}),
  }

  const res = await fetch(`${BASE}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

  if (!res.ok) {
    const text = await res.text().catch(() => 'Unknown error')
    throw new Error(`Server error ${res.status}: ${text}`)
  }

  const data = await res.json()
  sessionId = data.session_id
  return data
}

export async function fetchHistory() {
  if (!sessionId) return []

  const res = await fetch(`${BASE}/history/${sessionId}`)
  if (!res.ok) return []

  const data = await res.json()
  return data.messages ?? []
}

export async function checkHealth() {
  const res = await fetch('/health')
  return res.ok
}
