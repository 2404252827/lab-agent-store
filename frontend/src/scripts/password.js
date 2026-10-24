import { ElMessage } from 'element-plus'
import { updatePassword } from '@/api/user'

export default {
  data() {
    return {
      saving: false,
      form: {
        oldPassword: '',
        newPassword: '',
        confirmPassword: '',
      },
      rules: {
        oldPassword: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
        newPassword: [
          { required: true, message: '请输入新密码', trigger: 'blur' },
          { min: 6, message: '密码长度不能少于 6 位', trigger: 'blur' },
          {
            validator: (rule, value, callback) => {
              if (value && value === this.form.oldPassword) {
                callback(new Error('新密码不能与原密码相同'))
                return
              }

              callback()
            },
            trigger: 'blur',
          },
        ],
        confirmPassword: [
          { required: true, message: '请再次输入新密码', trigger: 'blur' },
          {
            validator: (rule, value, callback) => {
              if (value !== this.form.newPassword) {
                callback(new Error('两次输入的新密码不一致'))
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
    resetForm() {
      this.form.oldPassword = ''
      this.form.newPassword = ''
      this.form.confirmPassword = ''
      this.$refs.passwordForm?.clearValidate()
    },
    async submitPassword() {
      const valid = await this.$refs.passwordForm.validate().catch(() => false)
      if (!valid) return

      this.saving = true
      try {
        await updatePassword({
          old_password: this.form.oldPassword,
          new_password: this.form.newPassword,
        })

        this.resetForm()
        ElMessage.success('密码修改成功')
      } catch {
        // 错误提示由响应拦截器统一处理（如「原密码错误」）
      } finally {
        this.saving = false
      }
    },
  },
}