import request from '@/utils/request'

// 实验室列表（分页，keyword 模糊匹配名称）
export function getLabList(params) {
  return request.get('/api/lab/list', { params })
}

// 新增实验室
export function createLab(data) {
  return request.post('/api/lab', data)
}

// 更新实验室
export function updateLab(labId, data) {
  return request.put(`/api/lab/${labId}`, data)
}

// 删除实验室
export function deleteLab(labId) {
  return request.delete(`/api/lab/${labId}`)
}
