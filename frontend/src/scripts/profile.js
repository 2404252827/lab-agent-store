import { ElMessage } from 'element-plus'
import { getUserInfo, updateUserInfo } from '@/api/user'
import { resolveFileUrl, uploadFile } from '@/api/file'
import { updateUser, userInfo } from '@/utils/auth'

const MAX_AVATAR_SIZE = 2 * 1024 * 1024

function isImageFile(file) {
  if (file.type) return file.type.startsWith('image/')

  return /\.(jpe?g|png|gif|webp)$/i.test(file.name || '')
}

// 仅接受形如用户对象的响应，避免异常响应污染本地登录态
function isUserPayload(data) {
  return !!data && typeof data === 'object' && !Array.isArray(data)
}

export default {
  data() {
    return {
      user: null,
      saving: false,
      uploading: false,
      form: {
        nickname: '',
        email: '',
        phone: '',
      },
      rules: {
        nickname: [
          { required: true, message: '请输入昵称', trigger: 'blur' },
          { min: 2, max: 20, message: '昵称长度应为 2 到 20 个字符', trigger: 'blur' },
        ],
        email: [
          {
            validator: (rule, value, callback) => {
              if (!value) {
                callback()
                return
              }

              if (!/^[\w.+-]+@[\w-]+(\.[\w-]+)+$/.test(value)) {
                callback(new Error('请输入正确的邮箱地址'))
                return
              }

              callback()
            },
            trigger: 'blur',
          },
        ],
        phone: [
          {
            validator: (rule, value, callback) => {
              if (!value) {
                callback()
                return
              }

              if (!/^1[3-9]\d{9}$/.test(value)) {
                callback(new Error('请输入正确的手机号'))
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
  computed: {
    userName() {
      return this.user?.nickname || this.user?.username || '用户'
    },
    avatarUrl() {
      return resolveFileUrl(this.user?.avatar)
    },
  },
  mounted() {
    this.loadProfile()
  },
  methods: {
    // 回显用户信息，并同步到本地登录态
    applyUser(user) {
      this.user = user || null
      this.form.nickname = user?.nickname || ''
      this.form.email = user?.email || ''
      this.form.phone = user?.phone || ''
    },
    async loadProfile() {
      try {
        const data = await getUserInfo()

        if (!isUserPayload(data)) {
          this.applyUser(userInfo.value)
          return
        }

        updateUser(data)
        this.applyUser(data)
      } catch {
        // 请求失败时回退本地缓存（错误提示由响应拦截器统一处理）
        this.applyUser(userInfo.value)
      }
    },
    resetForm() {
      this.applyUser(this.user)
      this.$refs.profileForm?.clearValidate()
    },
    async submitProfile() {
      const valid = await this.$refs.profileForm.validate().catch(() => false)
      if (!valid) return

      this.saving = true
      try {
        // 后端 exclude_none，空字符串用于清空字段
        const data = await updateUserInfo({
          nickname: this.form.nickname,
          email: this.form.email,
          phone: this.form.phone,
        })

        if (isUserPayload(data)) {
          updateUser(data)
          this.applyUser(data)
        }

        ElMessage.success('个人信息已更新')
      } catch {
        // 错误提示由响应拦截器统一处理
      } finally {
        this.saving = false
      }
    },
    async requestAvatarUpload(options) {
      const file = options.file

      if (!isImageFile(file)) {
        ElMessage.error('头像仅支持图片格式')
        options.onError?.(new Error('头像仅支持图片格式'))
        return
      }

      if (file.size > MAX_AVATAR_SIZE) {
        ElMessage.error('头像大小不能超过 2MB')
        options.onError?.(new Error('头像大小不能超过 2MB'))
        return
      }

      this.uploading = true
      try {
        const fileRes = await uploadFile(file)
        const data = await updateUserInfo({ avatar: fileRes.url })

        // 只刷新头像，避免覆盖表单中尚未保存的昵称/邮箱/手机号
        if (isUserPayload(data)) {
          updateUser(data)
          this.user = data
        }

        options.onSuccess?.(fileRes)
        ElMessage.success('头像更新成功')
      } catch (error) {
        options.onError?.(error)
      } finally {
        this.uploading = false
      }
    },
  },
}
