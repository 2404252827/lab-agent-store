import { ref } from 'vue'

const TOKEN_KEY = 'lab_agent_token'
const USER_KEY = 'lab_agent_user'

function readStorage(key) {
  return localStorage.getItem(key) ?? sessionStorage.getItem(key)
}

function writeStorage(key, value, remember) {
  const primary = remember ? localStorage : sessionStorage
  const other = remember ? sessionStorage : localStorage

  primary.setItem(key, value)
  other.removeItem(key)
}

function removeStorage(key) {
  localStorage.removeItem(key)
  sessionStorage.removeItem(key)
}

// 判断当前登录态实际存放在哪个存储中（记住我 -> localStorage）
function activeStorage() {
  const inLocal = localStorage.getItem(TOKEN_KEY) !== null || localStorage.getItem(USER_KEY) !== null
  return inLocal ? localStorage : sessionStorage
}

function parseUser(raw) {
  if (!raw) return null

  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}

export const userInfo = ref(parseUser(readStorage(USER_KEY)))

export function getToken() {
  return readStorage(TOKEN_KEY) || ''
}

export function setToken(token, remember = false) {
  writeStorage(TOKEN_KEY, token, remember)
}

export function removeToken() {
  removeStorage(TOKEN_KEY)
}

export function getUser() {
  return userInfo.value
}

export function setUser(user, remember = false) {
  if (user == null) {
    removeUser()
    return
  }

  writeStorage(USER_KEY, JSON.stringify(user), remember)
  userInfo.value = user
}

// 局部更新用户信息，并写回当前登录态所在的存储位置，避免「记住我」的登录态被挤到 sessionStorage
export function updateUser(partial) {
  if (partial == null) return userInfo.value

  const merged = { ...(userInfo.value || {}) }

  Object.entries(partial).forEach(([key, value]) => {
    if (value !== undefined) merged[key] = value
  })

  const primary = activeStorage()
  const other = primary === localStorage ? sessionStorage : localStorage

  primary.setItem(USER_KEY, JSON.stringify(merged))
  other.removeItem(USER_KEY)
  userInfo.value = merged

  return merged
}

export function removeUser() {
  removeStorage(USER_KEY)
  userInfo.value = null
}

export function clearAuth() {
  removeToken()
  removeUser()

  // 兼容旧版本：AI 对话以前存在这个固定 key 里，
  // 不按用户区分，换用户会串数据，所以登出时一并清掉
  sessionStorage.removeItem('lab_agent_ai_messages')
}
