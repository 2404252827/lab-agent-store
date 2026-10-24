import request from '@/utils/request'
import { getToken } from '@/utils/auth'

// AI 相关请求都比较慢，单独放宽超时
const AI_TIMEOUT = 60000

// 读取当前登录用户的对话历史
// 后端按 JWT 里的 user_id 过滤，前端不需要（也不能）传用户标识
export function getChatHistory() {
  return request.get('/api/ai/history', { timeout: AI_TIMEOUT })
}

// 清空当前登录用户的对话历史
export function clearChatHistory() {
  return request.delete('/api/ai/history', { timeout: AI_TIMEOUT })
}

// 非流式对话（保留给调试用，页面走下面的流式接口）
export function chatWithAi(content) {
  return request.post('/api/ai/chat', { content }, { timeout: AI_TIMEOUT })
}

// 工具名 -> 中文提示，用于流式过程中显示「正在查询实验室…」
export const TOOL_LABELS = {
  get_current_date: '正在确认日期',
  query_labs: '正在查询实验室',
  query_equipment: '正在查询设备',
  query_my_reservations: '正在查询你的预约',
  create_lab_reservation: '正在提交预约',
  search_lab_rules: '正在查阅规则',
}

/**
 * 流式对话（SSE）
 *
 * 只传本次问题，历史由后端从 PostgreSQL 读取。
 *
 * 为什么不能用 axios：axios 默认会把整个响应体缓冲完再交给回调，拿不到增量。
 * 这里必须用 fetch + ReadableStream 手动读。
 *
 * 代价是绕过了 request.js 的拦截器，所以 401 和错误提示要自己处理。
 *
 * @param {string} content   本次提问
 * @param {Object} handlers  { onToken(text), onTool(name) }
 */
export async function streamChatWithAi(content, handlers = {}) {
  const { onToken, onTool } = handlers
  const base = import.meta.env.VITE_API_BASE_URL || ''
  const token = getToken()

  const resp = await fetch(`${base}/api/ai/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ content }),
  })

  // 流还没开始就失败时（401、参数错误等），仍然是普通的 HTTP 错误
  if (!resp.ok) {
    let message = `请求失败（${resp.status}）`

    try {
      const payload = await resp.json()
      message = payload?.message || message
    } catch {
      // 响应不是 JSON，用默认提示
    }

    // 401 要自己处理，行为和 request.js 保持一致：
    // 清登录态 + 跳登录页。动态 import 是为了避免和 router 形成循环依赖
    if (resp.status === 401) {
      const [{ clearAuth }, { default: router }] = await Promise.all([
        import('@/utils/auth'),
        import('@/router'),
      ])
      clearAuth()
      const current = router.currentRoute.value
      if (current.path !== '/login') {
        router.replace({ path: '/login', query: { redirect: current.fullPath } })
      }
    }

    throw new Error(message)
  }

  if (!resp.body) {
    throw new Error('当前浏览器不支持流式响应')
  }

  const reader = resp.body.getReader()
  // stream: true 表示后面还有数据，避免把一个多字节汉字从中间截断
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  // 处理一个 SSE 帧：形如 "data: {...}"
  const handleFrame = (frame) => {
    const line = frame.split('\n').find((item) => item.startsWith('data:'))
    if (!line) return

    let event
    try {
      event = JSON.parse(line.slice(5).trim())
    } catch {
      return
    }

    if (event.type === 'token') onToken?.(event.content)
    else if (event.type === 'tool') onTool?.(event.name)
    else if (event.type === 'error') throw new Error(event.message)
  }

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      // SSE 用空行分帧；有些代理会把 \n 变成 \r\n，这里统一一下
      buffer = buffer.replace(/\r\n/g, '\n')

      let index
      while ((index = buffer.indexOf('\n\n')) !== -1) {
        handleFrame(buffer.slice(0, index))
        buffer = buffer.slice(index + 2)
      }
    }

    // 收尾：处理最后一个没有以空行结尾的帧
    buffer += decoder.decode()
    if (buffer.trim()) handleFrame(buffer)
  } catch (error) {
    // 出错时主动断开，别让服务端继续生成
    try {
      await reader.cancel()
    } catch {
      // 忽略取消失败
    }
    throw error
  }
}