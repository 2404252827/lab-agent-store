import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'
import { clearAuth, getToken } from '@/utils/auth'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 10000
})
// 请求拦截器，向后端请求数据时把token放入请求头
request.interceptors.request.use(
  (config) => {
    const token = getToken()

    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    return config
  },
  (error) => Promise.reject(error)
)
// 响应拦截器，处理响应
request.interceptors.response.use(
  (response) => {
    const res = response.data

    // 非标准信封响应（例如文件流）直接返回
    if (res == null || typeof res !== 'object' || !('code' in res)) {
      return res
    }

    if (res.code === 200) {
      return res.data
    }

    const message = res.message || '请求失败'
    ElMessage.error(message)
    return Promise.reject(new Error(message))
  },
  (error) => {
    const status = error.response?.status
    const message = error.response?.data?.message

    if (status === 401) {
      clearAuth()
      ElMessage.error(message || '登录已失效，请重新登录')

      const current = router.currentRoute.value
      if (current.path !== '/login') {
        router.replace({ path: '/login', query: { redirect: current.fullPath } })
      }
    } else if (status) {
      // 后端返回了响应：优先用统一信封里的 message，5xx 再补上状态码，方便和后端日志对照
      ElMessage.error(
        status >= 500 && message ? `${message}（${status}）` : message || `请求失败（${status}）`
      )
    } else {
      // 完全没拿到响应（error.response 为空）分两种情况：
      // 1) 后端没启动 / 端口不通 / 超时；
      // 2) 响应被浏览器跨域策略拦截（后端未处理的 500 就属于这种），axios 同样表现为没有 response。
      const code = error.code

      if (code === 'ECONNABORTED' || code === 'ETIMEDOUT') {
        ElMessage.error('请求超时，请确认后端服务状态后重试')
      } else if (code === 'ERR_NETWORK') {
        ElMessage.error('无法连接后端服务（后端未启动、端口不通，或响应被跨域策略拦截）')
      } else {
        ElMessage.error('网络异常，请稍后重试')
      }
    }

    return Promise.reject(error)
  }
)

export default request
