import request from '@/utils/request'

// 文件写入（上传）接口
export function uploadFile(file) {
  const formData = new FormData()
  formData.append('file', file)

  // 不手动设置 Content-Type，交给浏览器补全 multipart boundary
  return request.post('/api/files/upload', formData)
}

// 把后端返回的相对文件地址转为可直接用于 <img> 的绝对地址
export function resolveFileUrl(path) {
  if (!path) return ''

  if (/^https?:\/\//i.test(path)) return path

  const baseURL = import.meta.env.VITE_API_BASE_URL || ''
  return `${baseURL}${path}`
}
