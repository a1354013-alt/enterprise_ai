import test from 'node:test'
import assert from 'node:assert/strict'

const storage = {
  data: new Map(),
  getItem(key) {
    return this.data.has(key) ? this.data.get(key) : null
  },
  setItem(key, value) {
    this.data.set(key, value)
  },
  removeItem(key) {
    this.data.delete(key)
  },
}

globalThis.localStorage = storage
class SimpleCustomEvent extends Event {
  constructor(type, options = {}) {
    super(type)
    this.detail = options.detail
  }
}

globalThis.CustomEvent = SimpleCustomEvent
if (!globalThis.addEventListener) {
  const target = new EventTarget()
  globalThis.addEventListener = target.addEventListener.bind(target)
  globalThis.removeEventListener = target.removeEventListener.bind(target)
  globalThis.dispatchEvent = target.dispatchEvent.bind(target)
}

const auth = await import('../src/auth.js')

test('token storage uses one persistent source', () => {
  auth.clearToken()
  auth.setToken('abc123')
  assert.equal(auth.getToken(), 'abc123')
  assert.equal(storage.getItem(auth.AUTH_STORAGE_KEY), 'abc123')
  auth.clearToken()
  assert.equal(auth.restoreToken(), null)
})

test('unauthorized event notifies listeners once and can be removed', () => {
  let detail = ''
  const cleanup = auth.onUnauthorized((event) => {
    detail = event.detail
  })
  auth.notifyUnauthorized('expired')
  assert.equal(detail, 'expired')
  cleanup()
  detail = ''
  auth.notifyUnauthorized('ignored')
  assert.equal(detail, '')
})
