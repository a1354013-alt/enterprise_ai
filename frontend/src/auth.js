export const AUTH_STORAGE_KEY = 'local-ai-engineer-workspace.authToken'
export const UNAUTHORIZED_EVENT = 'auth:unauthorized'

let currentToken = null

function getStorage() {
  if (typeof window !== 'undefined' && window.localStorage) {
    return window.localStorage
  }
  if (typeof globalThis !== 'undefined' && globalThis.localStorage) {
    return globalThis.localStorage
  }
  return null
}

function getEventTarget() {
  if (typeof window !== 'undefined' && window.dispatchEvent) {
    return window
  }
  if (typeof globalThis !== 'undefined' && globalThis.dispatchEvent) {
    return globalThis
  }
  return null
}

export function restoreToken() {
  const storage = getStorage()
  currentToken = storage?.getItem(AUTH_STORAGE_KEY) ?? null
  return currentToken
}

export function setToken(token) {
  currentToken = token || null
  const storage = getStorage()
  if (!storage) {
    return currentToken
  }
  if (currentToken) {
    storage.setItem(AUTH_STORAGE_KEY, currentToken)
  } else {
    storage.removeItem(AUTH_STORAGE_KEY)
  }
  return currentToken
}

export function clearToken() {
  return setToken(null)
}

export function getToken() {
  return currentToken
}

export function notifyUnauthorized(detail = 'Session expired.') {
  const target = getEventTarget()
  if (!target) {
    return
  }
  const event = typeof CustomEvent === 'function'
    ? new CustomEvent(UNAUTHORIZED_EVENT, { detail })
    : { type: UNAUTHORIZED_EVENT, detail }
  target.dispatchEvent(event)
}

export function onUnauthorized(handler) {
  const target = getEventTarget()
  if (!target || !target.addEventListener) {
    return () => {}
  }
  target.addEventListener(UNAUTHORIZED_EVENT, handler)
  return () => target.removeEventListener(UNAUTHORIZED_EVENT, handler)
}
