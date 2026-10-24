import { createRouter, createWebHistory } from 'vue-router'
import { getToken, userInfo } from '@/utils/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', redirect: '/login' },
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/Login.vue'),
      meta: { title: '登录' }
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('@/views/Register.vue'),
      meta: { title: '注册' }
    },
    {
      path: '/manager',
      name: 'Layout',
      component: () => import('@/layouts/Layout.vue'),
      children: [
        {
          path: 'home',
          name: 'Home',
          component: () => import('@/views/Home.vue'),
          meta: { title: '系统首页' }
        },
        {
          path: 'ai',
          name: 'Ai',
          component: () => import('@/views/Ai.vue'),
          meta: { title: 'AI 智能助手' }
        },
        {
          path: 'lab',
          name: 'Lab',
          component: () => import('@/views/Lab.vue'),
          meta: { title: '实验室管理' }
        },
        {
          path: 'equipment',
          name: 'Equipment',
          component: () => import('@/views/Equipment.vue'),
          meta: { title: '设备管理' }
        },
        {
          path: 'reservation',
          name: 'Reservation',
          component: () => import('@/views/Reservation.vue'),
          meta: { title: '预约管理' }
        },
        {
          path: 'user',
          name: 'User',
          component: () => import('@/views/User.vue'),
          meta: { title: '用户管理', requiresAdmin: true }
        },
        {
          path: 'profile',
          name: 'Profile',
          component: () => import('@/views/Profile.vue'),
          meta: { title: '个人信息' }
        },
        {
          path: 'password',
          name: 'Password',
          component: () => import('@/views/Password.vue'),
          meta: { title: '修改密码' }
        }
      ]
    }
  ]
})

const whiteList = ['/login', '/register']

// 路由守卫
router.beforeEach((to) => {
  const token = getToken()

  // 已登录：不再停留在登录页，直接进入系统
  if (token) {
    if (to.path === '/login') {
      return { path: '/manager/home' }
    }

    // 仅管理员可访问的页面：非管理员统一回首页，避免拿到「需要管理员权限」的报错
    if (to.meta.requiresAdmin && userInfo.value?.role !== 'admin') {
      return { path: '/manager/home' }
    }

    return true
  }

  // 未登录：白名单放行，其余跳登录页并记录来源
  if (whiteList.includes(to.path)) {
    return true
  }

  return { path: '/login', query: { redirect: to.fullPath } }
})

export default router
