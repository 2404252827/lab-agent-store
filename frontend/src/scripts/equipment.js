import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createEquipment,
  deleteEquipment,
  getEquipmentList,
  updateEquipment
} from '@/api/equipment'
import { getLabList } from '@/api/lab'
import { resolveFileUrl, uploadFile } from '@/api/file'
import { userInfo } from '@/utils/auth'

const MAX_IMAGE_SIZE = 2 * 1024 * 1024
const LAB_OPTIONS_PAGE_SIZE = 100

function isImageFile(file) {
  if (file.type) return file.type.startsWith('image/')

  return /\.(jpe?g|png|gif|webp)$/i.test(file.name || '')
}

function createEmptyForm() {
  return {
    lab_id: null,
    name: '',
    spec: '',
    quantity: 1,
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
      labOptions: [],
      query: {
        page: 1,
        page_size: 10,
        keyword: '',
        lab_id: null
      },
      dialogVisible: false,
      dialogMode: 'create',
      saving: false,
      uploading: false,
      editingId: null,
      form: createEmptyForm(),
      rules: {
        lab_id: [{ required: true, message: '请选择所属实验室', trigger: 'change' }],
        name: [
          { required: true, message: '请输入设备名称', trigger: 'blur' },
          { min: 1, max: 50, message: '名称长度应为 1 到 50 个字符', trigger: 'blur' }
        ],
        spec: [{ max: 100, message: '型号规格不能超过 100 个字符', trigger: 'blur' }]
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
        ? '维护设备的所属实验室、型号规格、数量与状态'
        : '查看实验室设备的型号规格、数量与状态'
    },
    dialogTitle() {
      return this.isEdit ? '编辑设备' : '新增设备'
    },
    coverUrl() {
      return resolveFileUrl(this.form.img)
    }
  },
  mounted() {
    this.loadList()
    this.loadLabs()
  },
  methods: {
    // 表格里逐行解析图片地址（模板中无法直接调用模块内导入的函数）
    coverSrc(path) {
      return resolveFileUrl(path)
    },

    // 列表查询

    async loadList() {
      this.loading = true
      try {
        const data = await getEquipmentList({
          page: this.query.page,
          page_size: this.query.page_size,
          keyword: this.query.keyword || undefined,
          lab_id: this.query.lab_id || undefined
        })

        this.list = Array.isArray(data?.list) ? data.list : []
        this.total = Number(data?.total) || 0
      } catch {
        // 错误提示由响应拦截器统一处理
      } finally {
        this.loading = false
      }
    },
    // 实验室下拉选项（用于筛选与表单选择）
    async loadLabs() {
      try {
        const data = await getLabList({ page: 1, page_size: LAB_OPTIONS_PAGE_SIZE })
        this.labOptions = Array.isArray(data?.list) ? data.list : []
      } catch {
        // 错误提示由响应拦截器统一处理
      }
    },
    handleSearch() {
      this.query.page = 1
      this.loadList()
    },
    resetSearch() {
      this.query.keyword = ''
      this.query.lab_id = null
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
      this.$nextTick(() => this.$refs.equipmentForm?.clearValidate())
    },
    openEdit(row) {
      this.dialogMode = 'edit'
      this.editingId = row.id
      this.form = {
        ...createEmptyForm(),
        lab_id: row.lab_id ?? null,
        name: row.name || '',
        spec: row.spec || '',
        quantity: row.quantity ?? 1,
        status: row.status === 0 ? 0 : 1,
        img: row.img || '',
        description: row.description || ''
      }
      this.dialogVisible = true
      this.$nextTick(() => this.$refs.equipmentForm?.clearValidate())
    },
    buildPayload() {
      return {
        lab_id: this.form.lab_id,
        name: this.form.name,
        spec: this.form.spec || '',
        quantity: this.form.quantity ?? 0,
        status: this.form.status,
        img: this.form.img || '',
        description: this.form.description || ''
      }
    },
    async submitForm() {
      const valid = await this.$refs.equipmentForm.validate().catch(() => false)
      if (!valid) return

      this.saving = true
      try {
        if (this.isEdit) {
          await updateEquipment(this.editingId, this.buildPayload())
        } else {
          await createEquipment(this.buildPayload())
          // 列表按 id 倒序，回到第一页即可看到新设备
          this.query.page = 1
        }

        this.dialogVisible = false
        ElMessage.success(this.isEdit ? '设备信息更新成功' : '新增设备成功')
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
        await ElMessageBox.confirm(`确定删除设备「${row.name}」吗？该操作不可恢复。`, '删除确认', {
          type: 'warning',
          confirmButtonText: '确定删除',
          cancelButtonText: '取消'
        })
      } catch {
        return // 用户取消
      }

      try {
        await deleteEquipment(row.id)

        // 删除当前页最后一条时回退一页，避免停留在空页
        if (this.list.length === 1 && this.query.page > 1) {
          this.query.page -= 1
        }

        ElMessage.success('删除设备成功')
        await this.loadList()
      } catch {
        // 错误提示由响应拦截器统一处理
      }
    },

    // 图片上传：先上传取到 url，随表单一起提交

    async requestCoverUpload(options) {
      const file = options.file

      if (!isImageFile(file)) {
        ElMessage.error('图片仅支持图片格式')
        options.onError?.(new Error('图片仅支持图片格式'))
        return
      }

      if (file.size > MAX_IMAGE_SIZE) {
        ElMessage.error('图片大小不能超过 2MB')
        options.onError?.(new Error('图片大小不能超过 2MB'))
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
