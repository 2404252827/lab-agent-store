import { ElMessage } from 'element-plus'
import { register } from '@/api/auth'

export default {
  data() {
    return {
      loading: false,
      form: {
        username: '',
        phone: '',
        password: '',
        confirmPassword: '',
      },
      rules: {
        username: [
          { required: true, message: '请输入用户名', trigger: 'blur' },
          { min: 2, max: 20, message: '用户名长度应为 2 到 20 个字符', trigger: 'blur' },
        ],
        phone: [
          { required: true, message: '请输入手机号', trigger: 'blur' },
          { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' },
        ],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' },
          { min: 6, message: '密码长度不能少于 6 位', trigger: 'blur' },
        ],
        confirmPassword: [
          { required: true, message: '请再次输入密码', trigger: 'blur' },
          {
            validator: (rule, value, callback) => {
              if (value !== this.form.password) {
                callback(new Error('两次输入的密码不一致'))
                return
              }
              callback()
            },
            trigger: 'blur',
          },
        ],
      },
    }
  },
  methods: {
    async submitRegister() {
      const valid = await this.$refs.registerForm.validate().catch(() => false)
      if (!valid) return

      this.loading = true
      try {
        await register({
          username: this.form.username,
          password: this.form.password,
          phone: this.form.phone,
        })

        ElMessage.success('注册成功，请登录')
        this.$router.push('/login')
      } catch {
        // 错误提示由响应拦截器统一处理（如「用户已存在」）
      } finally {
        this.loading = false
      }
    },
  },
}
