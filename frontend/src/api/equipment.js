import request from '@/utils/request'

// 设备列表（分页，keyword 模糊匹配设备名称，lab_id 按实验室筛选）
export function getEquipmentList(params) {
  return request.get('/api/equipment/list', { params })
}

// 新增设备
export function createEquipment(data) {
  return request.post('/api/equipment', data)
}

// 更新设备
export function updateEquipment(equipmentId, data) {
  return request.put(`/api/equipment/${equipmentId}`, data)
}

// 删除设备
export function deleteEquipment(equipmentId) {
  return request.delete(`/api/equipment/${equipmentId}`)
}
