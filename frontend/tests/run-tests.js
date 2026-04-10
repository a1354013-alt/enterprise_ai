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
const state = await import('../src/app-state.js')

function run(name, fn) {
  try {
    fn()
    console.log(`PASS ${name}`)
  } catch (error) {
    console.error(`FAIL ${name}`)
    console.error(error)
    process.exitCode = 1
  }
}

run('token storage uses one persistent source', () => {
  auth.clearToken()
  auth.setToken('abc123')
  assert.equal(auth.getToken(), 'abc123')
  assert.equal(storage.getItem(auth.AUTH_STORAGE_KEY), 'abc123')
  auth.clearToken()
  assert.equal(auth.restoreToken(), null)
})

run('unauthorized event notifies listeners once and can be removed', () => {
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

run('initial user state is empty and safe for boot', () => {
  assert.deepEqual(state.createInitialUser(), {
    user_id: '',
    role: '',
    display_name: '',
  })
})

run('initial UI state does not crash workspace init', () => {
  const ui = state.createInitialUiState()
  assert.deepEqual(ui.documents, [])
  assert.deepEqual(ui.uploadRoles, ['employee'])
  assert.equal(ui.selectedTemplate, '')
  assert.deepEqual(ui.templates, [])
})
