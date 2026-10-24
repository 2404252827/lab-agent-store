import request from '@/utils/request'

export function getUserInfo() {
  return request.get('/api/user/info')
}

export function updateUserInfo(data) {
  return request.put('/api/user/update', data)
}

export function updatePassword(data) {
  return request.put('/api/user/password', data)
}

// 用户列表（管理员）：分页，keyword 同时模糊匹配账号与昵称
export function getUserList(params) {
  return request.get('/api/user/list', { params })
}

// 新增用户（管理员）
export function createUser(data) {
  return request.post('/api/user', data)
}

// 更新用户（管理员）
export function updateUser(userId, data) {
  return request.put(`/api/user/${userId}`, data)
}

// 删除用户（管理员）
export function deleteUser(userId) {
  return request.delete(`/api/user/${userId}`)
}
