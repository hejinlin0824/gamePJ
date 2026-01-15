import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
  // === 状态 (State) ===
  const user = ref(null)
  const token = ref(localStorage.getItem('access_token') || '') // 初始化时尝试从本地缓存读取 Token
  const isLoggedIn = ref(!!token.value) // 如果有 Token，暂且认为已登录

  // ⚠️ 确保这里和你服务器的 IP:端口一致
  const API_URL = "http://134.175.64.205:8005/api/auth"

  // === 动作 (Actions) ===

  // 登录
  async function login(username, password) {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)

    try {
      const res = await fetch(`${API_URL}/login`, {
        method: 'POST',
        body: formData,
      })
      
      if (!res.ok) throw new Error('登录失败，请检查账号或密码')
      
      const data = await res.json()
      
      // 更新状态
      token.value = data.access_token
      user.value = {
        username: data.username,
        nickname: data.nickname,
        avatar: data.avatar
      }
      isLoggedIn.value = true
      
      // 持久化保存 Token，刷新页面不丢失
      localStorage.setItem('access_token', data.access_token)
      return { success: true }
    } catch (error) {
      console.error(error)
      return { success: false, msg: error.message }
    }
  }

  // 注册
  async function register(username, password, nickname) {
    try {
      const res = await fetch(`${API_URL}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password, nickname })
      })

      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || '注册失败')
      }
      return { success: true }
    } catch (error) {
      return { success: false, msg: error.message }
    }
  }

  // 登出
  function logout() {
    token.value = ''
    user.value = null
    isLoggedIn.value = false
    localStorage.removeItem('access_token')
  }

  return { user, token, isLoggedIn, login, register, logout }
})