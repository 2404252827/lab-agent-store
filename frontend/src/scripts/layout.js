import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { clearAuth, userInfo } from '@/utils/auth'
import { resolveFileUrl } from '@/api/file'

export default {
  setup() {
    const MOBILE_BREAKPOINT = 992
    const route = useRoute()
    const router = useRouter()
    const isCollapsed = ref(false)
    const isMobile = ref(false)
    const mobileMenuOpen = ref(false)

    const asideWidth = computed(() => (isCollapsed.value ? '72px' : '220px'))
    const pageTitle = computed(() => route.meta.title || '')
    const userName = computed(
      () => userInfo.value?.nickname || userInfo.value?.username || '用户',
    )
    const userRole = computed(() => userInfo.value?.role || '')
    // 仅用于前端展示控制，真正的权限由后端 get_admin 校验
    const isAdmin = computed(() => userInfo.value?.role === 'admin')
    const avatarUrl = computed(() => resolveFileUrl(userInfo.value?.avatar))

    const syncViewport = () => {
      isMobile.value = window.innerWidth < MOBILE_BREAKPOINT

      if (!isMobile.value) {
        mobileMenuOpen.value = false
      }
    }

    const toggleCollapse = () => {
      isCollapsed.value = !isCollapsed.value
    }

    const toggleMobileMenu = () => {
      mobileMenuOpen.value = !mobileMenuOpen.value
    }

    const closeMobileMenu = () => {
      mobileMenuOpen.value = false
    }

    const handleCommand = (command) => {
      if (command === 'profile') {
        router.push('/manager/profile')
        return
      }

      if (command === 'password') {
        router.push('/manager/password')
        return
      }

      if (command === 'logout') {
        clearAuth()
        router.replace('/login')
      }
    }

    watch(() => route.path, closeMobileMenu)

    onMounted(() => {
      syncViewport()
      window.addEventListener('resize', syncViewport)
    })

    onBeforeUnmount(() => {
      window.removeEventListener('resize', syncViewport)
    })

    return {
      route,
      isCollapsed,
      isMobile,
      mobileMenuOpen,
      asideWidth,
      pageTitle,
      userName,
      userRole,
      isAdmin,
      avatarUrl,
      toggleCollapse,
      toggleMobileMenu,
      closeMobileMenu,
      handleCommand,
    }
  },
}
