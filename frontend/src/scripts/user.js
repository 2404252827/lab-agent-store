import { ElMessage, ElMessageBox } from 'element-plus'
import { createUser, deleteUser, getUserList, updateUser } from '@/api/user'
import { resolveFileUrl, uploadFile } from '@/api/file'

const MAX_AVATAR_SIZE = 2 * 1024 * 1024
const DEFAULT_PASSWORD = '111111'

// 列表接口已过滤 admin，这里只需要维护学生角色
const ROLE_OPTIONS = [{ label: '学生', value: 'student' }]

const ROLE_LABELS = ROLE_OPTIONS.reduce((map, item) => {
  map[item.value] = item.label
  return map
}, {})

function isImageFile(file) {
  if (file.type) return file.type.startsWith('image/')

  return /\.(jpe?g|png|gif|webp)$/i.test(file.name || '')
}

// 邮箱、手机号为选填项，留空即视为清空该字段
function validateOptionalEmail(rule, value, callback) {
  if (!value || /^[\w.+-]+@[\w-]+(\.[\w-]+)+$/.test(value)) {
    callback()
    return
  }

  callback(new Error('请输入正确的邮箱地址'))
}

function validateOptionalPhone(rule, value, callback) {
  if (!value || /^1[3-9]\d{9}$/.test(value)) {
    callback()
    return
  }

  callback(new Error('请输入正确的手机号'))
}

function createEmptyForm() {
  return {
    username: '',
    password: DEFAULT_PASSWORD,
    nickname: '',
    role: 'student',
    email: '',
    phone: '',
    avatar: '',
    status: 1
  }
}

export default {
  data() {
    return {
      loading: false,
      list: [],
      total: 0,
      query: {
        page: 1,
        page_size: 10,
        keyword: ''
      },
      roleOptions: ROLE_OPTIONS,
      dialogVisible: false,
      dialogMode: 'create',
      saving: false,
      uploading: false,
      editingId: null,
      form: createEmptyForm(),
      rules: {
        username: [
          { required: true, message: '请输入账号', trigger: 'blur' },
          { min: 2, max: 20, message: '账号长度应为 2 到 20 个字符', trigger: 'blur' }
        ],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' },
          { min: 6, message: '密码长度不能少于 6 位', trigger: 'blur' }
        ],
        nickname: [
          { required: true, message: '请输入昵称', trigger: 'blur' },
          { min: 2, max: 20, message: '昵称长度应为 2 到 20 个字符', trigger: 'blur' }
        ],
        email: [{ validator: validateOptionalEmail, trigger: 'blur' }],
        phone: [{ validator: validateOptionalPhone, trigger: 'blur' }]
      }
    }
  },
  computed: {
    isEdit() {
      return this.dialogMode === 'edit'
    },
    dialogTitle() {
      return this.isEdit ? '编辑用户' : '新增用户'
    },
    avatarUrl() {
      return resolveFileUrl(this.form.avatar)
    }
  },
  mounted() {
    this.loadList()
  },
  methods: {
    roleLabel(role) {
      return ROLE_LABELS[role] || role || '-'
    },

    // 列表查询

    async loadList() {
      this.loading = true
      try {
        const data = await getUserList({
          page: this.query.page,
          page_size: this.query.page_size,
          keyword: this.query.keyword || undefined
        })

        this.list = Array.isArray(data?.list) ? data.list : []
        this.total = Number(data?.total) || 0
      } catch {
        // 错误提示由响应拦截器统一处理
      } finally {
        this.loading = false
      }
    },
    handleSearch() {
      this.query.page = 1
      this.loadList()
    },
    resetSearch() {
      this.query.keyword = ''
      this.query.page = 1
      this.loadList()
    },
    handlePageChange(page) {
      this.query.page = page
      this.loadList()
    },
    handleSizeChange(size) {
      this.query.page_size = size
      this.query.page = 1
      this.loadList()
    },

    // 新增 / 编辑

    openCreate() {
      this.dialogMode = 'create'
      this.editingId = null
      this.form = createEmptyForm()
      this.dialogVisible = true
      this.$nextTick(() => this.$refs.userForm?.clearValidate())
    },
    openEdit(row) {
      this.dialogMode = 'edit'
      this.editingId = row.id
      this.form = {
        ...createEmptyForm(),
        username: row.username,
        nickname: row.nickname || '',
        role: row.role || 'student',
        email: row.email || '',
        phone: row.phone || '',
        avatar: row.avatar || '',
        status: row.status === 0 ? 0 : 1
      }
      this.dialogVisible = true
      this.$nextTick(() => this.$refs.userForm?.clearValidate())
    },
    // 新增需要账号与密码，编辑仅提交用户可改字段（后端 exclude_none）
    buildPayload() {
      const payload = {
        nickname: this.form.nickname,
        role: this.form.role,
        email: this.form.email,
        phone: this.form.phone,
        avatar: this.form.avatar,
        status: this.form.status
      }

      if (!this.isEdit) {
        payload.username = this.form.username
        payload.password = this.form.password
      }

      return payload
    },
    async submitForm() {
      const valid = await this.$refs.userForm.validate().catch(() => false)
      if (!valid) return

      this.saving = true
      try {
        if (this.isEdit) {
          await updateUser(this.editingId, this.buildPayload())
        } else {
          await createUser(this.buildPayload())
          // 列表按 id 倒序，回到第一页即可看到新用户
          this.query.page = 1
        }

        this.dialogVisible = false
        ElMessage.success(this.isEdit ? '用户信息更新成功' : '新增用户成功')
        await this.loadList()
      } catch {
        // 错误提示由响应拦截器统一处理
      } finally {
        this.saving = false
      }
    },

    // 删除

    async handleDelete(row) {
      try {
        await ElMessageBox.confirm(
          `确定删除用户「${row.nickname || row.username}」吗？该操作不可恢复。`,
          '删除确认',
          { type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消' }
        )
      } catch {
        return // 用户取消
      }

      try {
        await deleteUser(row.id)

        // 删除当前页最后一条时回退一页，避免停留在空页
        if (this.list.length === 1 && this.query.page > 1) {
          this.query.page -= 1
        }

        ElMessage.success('删除用户成功')
        await this.loadList()
      } catch {
        // 错误提示由响应拦截器统一处理
      }
    },

    // 头像上传：先上传取到 url，随表单一起提交

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
        this.form.avatar = fileRes.url
        options.onSuccess?.(fileRes)
      } catch (error) {
        options.onError?.(error)
      } finally {
        this.uploading = false
      }
    },
    clearAvatar() {
      this.form.avatar = ''
    }
  }
}
