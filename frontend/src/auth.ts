export const AUTH_STORAGE_KEY = 'knowledge-workspace.authToken'
export const UNAUTHORIZED_EVENT = 'auth:unauthorized'

let currentToken: string | null = null

type StorageLike = Pick<Storage, 'getItem' | 'setItem' | 'removeItem'>

function getStorage(): StorageLike | null {
  try {
    if (typeof window !== 'undefined') {
      return window.localStorage as StorageLike
    }
  } catch {
    // ignore
  }
  const candidate = (globalThis as unknown as { localStorage?: unknown }).localStorage as Partial<StorageLike> | undefined
  if (candidate?.getItem && candidate?.setItem && candidate?.removeItem) {
    return candidate as StorageLike
  }
  return null
}

function getEventTarget(): EventTarget | null {
  if (typeof window !== 'undefined') {
    return window as unknown as EventTarget
  }
  return globalThis as unknown as EventTarget
}

export function restoreToken() {
  const storage = getStorage()
  currentToken = storage?.getItem(AUTH_STORAGE_KEY) ?? null
  return currentToken
}

export function setToken(token: string | null) {
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

export function notifyUnauthorized(detail: string = 'Session expired.') {
  const target = getEventTarget()
  if (!target) {
    return
  }
  let event: Event
  if (typeof CustomEvent === 'function') {
    event = new CustomEvent<string>(UNAUTHORIZED_EVENT, { detail })
  } else {
    event = new Event(UNAUTHORIZED_EVENT)
    ;(event as unknown as { detail: string }).detail = detail
  }
  target.dispatchEvent(event)
}

export function onUnauthorized(handler: (event: CustomEvent<string> & { detail: string }) => void) {
  const target = getEventTarget()
  if (!target || !(target as unknown as { addEventListener?: unknown }).addEventListener) {
    return () => {}
  }
  const listener = (event: Event) => handler(event as CustomEvent<string> & { detail: string })
  ;(target as unknown as { addEventListener: (type: string, cb: (event: Event) => void) => void }).addEventListener(
    UNAUTHORIZED_EVENT,
    listener
  )
  return () => {
    ;(target as unknown as { removeEventListener: (type: string, cb: (event: Event) => void) => void }).removeEventListener(
      UNAUTHORIZED_EVENT,
      listener
    )
  }
}
