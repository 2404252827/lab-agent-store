import { ElMessage, ElMessageBox } from 'element-plus'
import { createLab, deleteLab, getLabList, updateLab } from '@/api/lab'
import { resolveFileUrl, uploadFile } from '@/api/file'
import { createReservation, getReservedLabDate } from '@/api/reservation'
import { userInfo } from '@/utils/auth'

const MAX_IMAGE_SIZE = 2 * 1024 * 1024

function isImageFile(file) {
  if (file.type) return file.type.startsWith('image/')

  return /\.(jpe?g|png|gif|webp)$/i.test(file.name || '')
}

// 把日期对象统一成 YYYY-MM-DD（接口返回的日期也是这个格式）
function toDateKey(value) {
  const date = new Date(value)
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')

  return `${date.getFullYear()}-${month}-${day}`
}

function createEmptyReserveForm() {
  return {
    lab_id: null,
    lab_name: '',
    lab_location: '',
    open_time: '',
    close_time: '',
    date: '',
    start_time: '',
    end_time: '',
    remark: ''
  }
}

function createEmptyForm() {
  return {
    name: '',
    location: '',
    capacity: 0,
    open_time: '08:00',
    close_time: '22:00',
    status: 1,
    img: '',
    description: ''
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
      dialogVisible: false,
      dialogMode: 'create',
      saving: false,
      uploading: false,
      editingId: null,
      form: createEmptyForm(),
      reserveVisible: false,
      reserving: false,
      reservedDates: [],
      reserveForm: createEmptyReserveForm(),
      reserveRules: {
        date: [{ required: true, message: '请选择预约日期', trigger: 'change' }],
        start_time: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
        // "HH:MM" 零补齐后可直接按字符串比较
        end_time: [
          { required: true, message: '请选择结束时间', trigger: 'change' },
          {
            validator: (rule, value, callback) => {
              if (!value || !this.reserveForm.start_time || value > this.reserveForm.start_time) {
                callback()
                return
              }

              callback(new Error('结束时间需要晚于开始时间'))
            },
            trigger: 'change'
          }
        ]
      },
      rules: {
        name: [
          { required: true, message: '请输入实验室名称', trigger: 'blur' },
          { min: 2, max: 50, message: '名称长度应为 2 到 50 个字符', trigger: 'blur' }
        ],
        location: [
          { required: true, message: '请输入实验室位置', trigger: 'blur' },
          { max: 100, message: '位置不能超过 100 个字符', trigger: 'blur' }
        ],
        // "HH:MM" 零补齐后可直接按字符串比较
        close_time: [
          {
            validator: (rule, value, callback) => {
              if (!value || !this.form.open_time || value > this.form.open_time) {
                callback()
                return
              }

              callback(new Error('结束时间需要晚于开放时间'))
            },
            trigger: 'change'
          }
        ]
      }
    }
  },
  computed: {
    isEdit() {
      return this.dialogMode === 'edit'
    },
    // 列表所有登录用户都能看，但新增/编辑/删除只有管理员可以
    isAdmin() {
      return userInfo.value?.role === 'admin'
    },
    subtitle() {
      return this.isAdmin
        ? '维护实验室的名称、位置、容量与开放时间'
        : '查看实验室信息、开放时间与容量'
    },
    reserveStartTime() {
      return this.reserveForm.open_time || '00:00'
    },
    reserveEndTime() {
      return this.reserveForm.close_time || '23:30'
    },
    reserveTimeRange() {
      const { open_time: open, close_time: close } = this.reserveForm

      if (open && close) return `${open} - ${close}`

      return open || close || '不限'
    },
    dialogTitle() {
      return this.isEdit ? '编辑实验室' : '新增实验室'
    },
    coverUrl() {
      return resolveFileUrl(this.form.img)
    }
  },
  mounted() {
    this.loadList()
  },
  methods: {
    // 表格里逐行解析封面地址（模板中无法直接调用模块内导入的函数）
    coverSrc(path) {
      return resolveFileUrl(path)
    },
    timeRange(row) {
      const { open_time: open, close_time: close } = row

      if (open && close) return `${open} - ${close}`

      return open || close || '-'
    },

    // 列表查询

    async loadList() {
      this.loading = true
      try {
        const data = await getLabList({
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
      this.$nextTick(() => this.$refs.labForm?.clearValidate())
    },
    openEdit(row) {
      this.dialogMode = 'edit'
      this.editingId = row.id
      this.form = {
        ...createEmptyForm(),
        name: row.name || '',
        location: row.location || '',
        capacity: row.capacity ?? 0,
        open_time: row.open_time || '',
        close_time: row.close_time || '',
        status: row.status === 0 ? 0 : 1,
        img: row.img || '',
        description: row.description || ''
      }
      this.dialogVisible = true
      this.$nextTick(() => this.$refs.labForm?.clearValidate())
    },
    buildPayload() {
      return {
        name: this.form.name,
        location: this.form.location,
        capacity: this.form.capacity || 0,
        open_time: this.form.open_time || '',
        close_time: this.form.close_time || '',
        img: this.form.img || '',
        description: this.form.description || '',
        // 后端 LabUpdateRequest 的 status 默认值为 1（不会被 exclude_none 过滤），
        // 所以更新时必须显式回传当前状态，否则会把「关闭」的实验室重置为「开放」
        status: this.form.status
      }
    },
    async submitForm() {
      const valid = await this.$refs.labForm.validate().catch(() => false)
      if (!valid) return

      this.saving = true
      try {
        if (this.isEdit) {
          await updateLab(this.editingId, this.buildPayload())
        } else {
          await createLab(this.buildPayload())
          // 列表按 id 倒序，回到第一页即可看到新实验室
          this.query.page = 1
        }

        this.dialogVisible = false
        ElMessage.success(this.isEdit ? '实验室信息更新成功' : '新增实验室成功')
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
          `确定删除实验室「${row.name}」吗？该操作不可恢复。`,
          '删除确认',
          {
            type: 'warning',
            confirmButtonText: '确定删除',
            cancelButtonText: '取消'
          }
        )
      } catch {
        return // 用户取消
      }

      try {
        await deleteLab(row.id)

        // 删除当前页最后一条时回退一页，避免停留在空页
        if (this.list.length === 1 && this.query.page > 1) {
          this.query.page -= 1
        }

        ElMessage.success('删除实验室成功')
        await this.loadList()
      } catch {
        // 错误提示由响应拦截器统一处理
      }
    },

    // 预约实验室

    async openReservation(row) {
      this.reserveForm = {
        ...createEmptyReserveForm(),
        lab_id: row.id,
        lab_name: row.name,
        lab_location: row.location || '',
        open_time: row.open_time || '',
        close_time: row.close_time || ''
      }
      this.reserveVisible = true
      this.$nextTick(() => this.$refs.reserveForm?.clearValidate())
      await this.loadReservedDates(row.id)
    },
    // 已预约的日期用于日期面板标红：只提示不阻止选择，时段冲突由后端校验
    async loadReservedDates(labId) {
      this.reservedDates = []

      try {
        const dates = await getReservedLabDate(labId)
        this.reservedDates = Array.isArray(dates) ? dates : []
      } catch {
        // 错误提示由响应拦截器统一处理
      }
    },
    // 与后端规则一致：至少提前一天，今天及更早的日期不可选
    disabledReserveDate(value) {
      return toDateKey(value) <= toDateKey(new Date())
    },
    reserveCellClass(value) {
      return this.reservedDates.includes(toDateKey(value)) ? 'booked-date-cell' : ''
    },
    async submitReservation() {
      const valid = await this.$refs.reserveForm.validate().catch(() => false)
      if (!valid) return

      this.reserving = true
      try {
        await createReservation({
          lab_id: this.reserveForm.lab_id,
          date: this.reserveForm.date,
          start_time: this.reserveForm.start_time,
          end_time: this.reserveForm.end_time,
          remark: this.reserveForm.remark
        })

        ElMessage.success('预约成功')
        this.reserveVisible = false
        // 重新拉取一次日期，保证下次打开时该日期已经标红
        await this.loadReservedDates(this.reserveForm.lab_id)
      } catch {
        // 错误提示由响应拦截器统一处理
      } finally {
        this.reserving = false
      }
    },

    // 封面上传：先上传取到 url，随表单一起提交

    async requestCoverUpload(options) {
      const file = options.file

      if (!isImageFile(file)) {
        ElMessage.error('封面仅支持图片格式')
        options.onError?.(new Error('封面仅支持图片格式'))
        return
      }

      if (file.size > MAX_IMAGE_SIZE) {
        ElMessage.error('封面大小不能超过 2MB')
        options.onError?.(new Error('封面大小不能超过 2MB'))
        return
      }

      this.uploading = true
      try {
        const fileRes = await uploadFile(file)
        this.form.img = fileRes.url
        options.onSuccess?.(fileRes)
      } catch (error) {
        options.onError?.(error)
      } finally {
        this.uploading = false
      }
    },
    clearCover() {
      this.form.img = ''
    }
  }
}
