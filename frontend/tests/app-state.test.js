import test from 'node:test'
import assert from 'node:assert/strict'

const { createInitialUiState, createInitialUser } = await import('../src/app-state.js')

test('initial user state is empty and safe for boot', () => {
  assert.deepEqual(createInitialUser(), {
    user_id: '',
    role: '',
    display_name: '',
  })
})

test('initial UI state does not crash workspace init', () => {
  const state = createInitialUiState()
  assert.deepEqual(state.documents, [])
  assert.deepEqual(state.photos, [])
  assert.equal(state.activeSection, 'knowledge')
  assert.deepEqual(state.knowledge.sources, [])
  assert.deepEqual(state.logbook.entries, [])
})
