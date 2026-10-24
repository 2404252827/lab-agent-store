import request from '@/utils/request'

// 预约实验室
export function createReservation(data) {
  return request.post('/api/reservation', data)
}

// 预约列表（分页）：管理员得到全部预约，学生得到自己的预约
export function getReservationList(params) {
  return request.get('/api/reservation/list', { params })
}

// 某个实验室已被预约的日期（供日期选择器标红）
export function getReservedLabDate(labId) {
  return request.get('/api/reservation/dates', { params: { lab_id: labId } })
}

// 取消预约（仅限本人、待审核状态的预约）
export function cancelReservation(reservationId) {
  return request.put(`/api/reservation/${reservationId}/cancel`)
}

// 审核预约（管理员）：status 1-同意，2-驳回
export function auditReservation(reservationId, data) {
  return request.put(`/api/reservation/${reservationId}/audit`, data)
}
