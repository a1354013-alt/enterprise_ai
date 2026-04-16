import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'

import LogbookPanel from '../src/components/LogbookPanel.vue'
import { PrimeStubs } from './stubs'

vi.mock('primevue/usetoast', () => ({
  useToast: () => ({ add: vi.fn() }),
}))

const mocks = vi.hoisted(() => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}))

vi.mock('../src/api', () => ({
  apiClient: mocks.apiClient,
}))

describe('LogbookPanel flows', () => {
  it('creates logbook entry with status/source/related_item_ids', async () => {
    const apiClient = mocks.apiClient
    apiClient.post.mockResolvedValueOnce({ message: 'ok' })
    apiClient.get.mockResolvedValueOnce([])

    const wrapper = mount(LogbookPanel, { global: { stubs: PrimeStubs } })

    wrapper.vm.form.title = 'T'
    wrapper.vm.form.problem = 'P'
    wrapper.vm.form.solution = 'S'
    wrapper.vm.form.status = 'draft'
    wrapper.vm.form.source_type = 'autotest-derived'
    wrapper.vm.form.source_ref = 'autotest_run:r1'
    wrapper.vm.form.related_item_ids = ['autotest_run:r1']

    await wrapper.vm.saveEntry()

    expect(apiClient.post).toHaveBeenCalledWith('/api/logbook/entries', expect.any(Object))
    const payload = apiClient.post.mock.calls[0][1]
    expect(payload).toMatchObject({
      title: 'T',
      problem: 'P',
      solution: 'S',
      status: 'draft',
      source_type: 'autotest-derived',
      source_ref: 'autotest_run:r1',
      related_item_ids: ['autotest_run:r1'],
    })
  })

  it('promotes entry to knowledge', async () => {
    const apiClient = mocks.apiClient
    apiClient.post.mockResolvedValueOnce({ knowledge_entry_id: 'k1' })
    apiClient.get.mockResolvedValueOnce([])

    const wrapper = mount(LogbookPanel, { global: { stubs: PrimeStubs } })
    await wrapper.vm.promoteEntry({ id: 'l1', title: 'T' })

    expect(apiClient.post).toHaveBeenCalledWith('/api/logbook/entries/l1/promote-to-knowledge')
  })
})
