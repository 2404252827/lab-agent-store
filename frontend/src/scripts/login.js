import { ElMessage } from 'element-plus'
import { login } from '@/api/auth'
import { setToken, setUser } from '@/utils/auth'

export default {
  data() {
    return {
      loading: false,
      form: {
        username: '',
        password: '',
        remember: true,
      },
      rules: {
        username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' },
          { min: 6, message: '密码长度不能少于 6 位', trigger: 'blur' },
        ],
      },
    }
  },
  methods: {
    async submitLogin() {
      const valid = await this.$refs.loginForm.validate().catch(() => false)
      if (!valid) return

      this.loading = true
      try {
        const data = await login({
          username: this.form.username,
          password: this.form.password,
        })

        setToken(data.token, this.form.remember)
        setUser(data.user, this.form.remember)
        ElMessage.success('登录成功')
        this.$router.push(this.$route.query.redirect || '/manager/home')
      } catch {
        // 错误提示由响应拦截器统一处理
      } finally {
        this.loading = false
      }
    },
    handleForgotPassword() {
      ElMessage.info('请联系系统管理员重置密码')
    },
  },
}
