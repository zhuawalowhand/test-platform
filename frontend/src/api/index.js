import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// 请求拦截器
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器
api.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response) {
      const { status, data, config } = error.response
      const isAuthRequest = config?.url?.includes('/users/login') || config?.url?.includes('/users/register')
      if ((status === 401 || status === 403) && !isAuthRequest) {
        localStorage.removeItem('token')
        router.push('/login')
        ElMessage.error('登录已过期，请重新登录')
      } else {
        ElMessage.error(data.detail || '请求失败')
      }
    } else {
      ElMessage.error('网络错误')
    }
    return Promise.reject(error)
  }
)

// 用户相关
export const userApi = {
  login: (data) => api.post('/users/login', data),
  register: (data) => api.post('/users/register', data),
  getMe: () => api.get('/users/me'),
  update: (data) => api.put('/users/me', data)
}

// 用例相关
export const testcaseApi = {
  list: (params) => api.get('/testcases/', { params }),
  get: (id) => api.get(`/testcases/${id}`),
  create: (data) => api.post('/testcases/', data),
  update: (id, data) => api.put(`/testcases/${id}`, data),
  delete: (id) => api.delete(`/testcases/${id}`),
  tags: () => api.get('/testcases/tags'),
  reorder: (order) => api.post('/testcases/reorder', order)
}

// 执行相关
export const executeApi = {
  run: (data) => api.post('/execute/', data),
  reports: (params) => api.get('/execute/reports', { params }),
  reportDetail: (id) => api.get(`/execute/reports/${id}`),
  stats: () => api.get('/execute/stats/summary'),
  testWebhook: (webhookUrl) => api.post('/execute/webhook/test', null, { params: { webhook_url: webhookUrl } })
}

// 环境相关
export const environmentApi = {
  list: () => api.get('/environments/'),
  get: (id) => api.get(`/environments/${id}`),
  create: (data) => api.post('/environments/', data),
  update: (id, data) => api.put(`/environments/${id}`, data),
  delete: (id) => api.delete(`/environments/${id}`)
}

// 定时任务
export const scheduleApi = {
  list: () => api.get('/schedules/'),
  get: (id) => api.get(`/schedules/${id}`),
  create: (data) => api.post('/schedules/', data),
  update: (id, data) => api.put(`/schedules/${id}`, data),
  delete: (id) => api.delete(`/schedules/${id}`),
  toggle: (id) => api.patch(`/schedules/${id}/toggle`),
  run: (id) => api.post(`/schedules/${id}/run`),
  schedulerStatus: () => api.get('/scheduler/status')
}

export default api
