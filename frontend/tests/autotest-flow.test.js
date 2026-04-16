import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'

import AutoTestPanel from '../src/components/AutoTestPanel.vue'
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

describe('AutoTestPanel flows', () => {
  it('runs autotest upload and loads run details', async () => {
    const apiClient = mocks.apiClient
    apiClient.post.mockResolvedValueOnce({ id: 'r1', status: 'passed' })
    apiClient.get.mockResolvedValueOnce([]) // initial loadRuns on mount
    apiClient.get.mockResolvedValueOnce([]) // loadRuns after run
    apiClient.get.mockResolvedValueOnce({ id: 'r1', steps: [], status: 'passed' }) // fetch run

    const wrapper = mount(AutoTestPanel, { global: { stubs: PrimeStubs } })
    wrapper.vm.selectedZip = new File(['zip'], 'proj.zip', { type: 'application/zip' })

    await wrapper.vm.runAutoTest()

    expect(apiClient.post.mock.calls[0][0]).toBe('/api/autotest/run')
    expect(apiClient.get).toHaveBeenCalledWith('/api/autotest/runs/r1')
  })
})
