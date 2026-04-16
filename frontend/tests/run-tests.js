import assert from 'node:assert/strict'

import { readFile } from 'node:fs/promises'

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
const api = await import('../src/api.js')

async function run(name, fn) {
  try {
    await fn()
    console.log(`PASS ${name}`)
  } catch (error) {
    console.error(`FAIL ${name}`)
    console.error(error)
    process.exitCode = 1
  }
}

await run('token storage uses one persistent source', () => {
  auth.clearToken()
  auth.setToken('abc123')
  assert.equal(auth.getToken(), 'abc123')
  assert.equal(storage.getItem(auth.AUTH_STORAGE_KEY), 'abc123')
  auth.clearToken()
  assert.equal(auth.restoreToken(), null)
})

await run('unauthorized event notifies listeners once and can be removed', () => {
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

await run('initial user state is empty and safe for boot', () => {
  assert.deepEqual(state.createInitialUser(), {
    user_id: '',
    role: '',
    display_name: '',
  })
})

await run('initial UI state does not crash workspace init', () => {
  const ui = state.createInitialUiState()
  assert.deepEqual(ui.documents, [])
  assert.deepEqual(ui.photos, [])
  assert.equal(ui.activeSection, 'knowledge')
  assert.deepEqual(ui.knowledge.sources, [])
  assert.deepEqual(ui.logbook.entries, [])
})

await run('bootstrap session clears token on any non-login 401', async () => {
  auth.clearToken()
  auth.setToken('token123')

  const handler = api.apiClient.interceptors.response.handlers.find((item) => typeof item?.rejected === 'function')?.rejected
  assert.equal(typeof handler, 'function')

  await handler({
    response: { status: 401, data: { detail: 'unauthorized' } },
    config: { url: '/api/docs' },
    message: 'unauthorized',
  }).catch(() => {})
  assert.equal(auth.getToken(), null)

  auth.setToken('token123')
  await handler({
    response: { status: 401, data: { detail: 'bad creds' } },
    config: { url: '/api/login' },
    message: 'unauthorized',
  }).catch(() => {})
  assert.equal(auth.getToken(), 'token123')
})

await run('autotest panel uses /api/autotest and project_name field', async () => {
  const contents = await readFile(new URL('../src/components/AutoTestPanel.vue', import.meta.url), 'utf-8')
  assert.ok(contents.includes('/api/autotest/run'))
  assert.ok(contents.includes('/api/autotest/runs'))
  assert.ok(contents.includes('project_name'))
})
