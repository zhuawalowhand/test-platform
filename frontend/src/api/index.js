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
      const { status, data } = error.response
      if (status === 401 || status === 403) {
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
  getMe: () => api.get('/users/me')
}

// 用例相关
export const testcaseApi = {
  list: (params) => api.get('/testcases/', { params }),
  get: (id) => api.get(`/testcases/${id}`),
  create: (data) => api.post('/testcases/', data),
  update: (id, data) => api.put(`/testcases/${id}`, data),
  delete: (id) => api.delete(`/testcases/${id}`)
}

// 执行相关
export const executeApi = {
  run: (data) => api.post('/execute/', data),
  reports: (params) => api.get('/execute/reports', { params }),
  reportDetail: (id) => api.get(`/execute/reports/${id}`)
}

export default api
