import axios from 'axios'
import { clearToken, getToken, notifyUnauthorized } from './auth'

const API_BASE_URL = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
})

apiClient.interceptors.request.use((config) => {
  const token = getToken()
  if (!config.skipAuth && token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const status = error.response?.status ?? 0
    const detail = error.response?.data?.detail || error.message || 'Request failed.'

    if (status === 401) {
      clearToken()
      notifyUnauthorized(detail)
    }

    return Promise.reject({
      status,
      message: detail,
    })
  }
)
