import { ElMessage, ElMessageBox } from 'element-plus'
import { auditReservation, cancelReservation, getReservationList } from '@/api/reservation'
import { getLabList } from '@/api/lab'
import { userInfo } from '@/utils/auth'

const LAB_OPTIONS_PAGE_SIZE = 100

const STATUS_LABELS = {
  0: '待审核',
  1: '已同意',
  2: '已驳回',
  3: '已取消'
}

const STATUS_TAG_TYPES = {
  0: 'warning',
  1: 'success',
  2: 'danger',
  3: 'info'
}

export default {
  data() {
    return {
      loading: false,
      list: [],
      total: 0,
      labOptions: [],
      statusTabs: [
        { label: '全部', value: 'all' },
        { label: '待审核', value: '0' },
        { label: '已同意', value: '1' },
        { label: '已驳回', value: '2' },
        { label: '已取消', value: '3' }
      ],
      query: {
        page: 1,
        page_size: 10,
        status: 'all',
        lab_id: null
      }
    }
  },
  computed: {
    isAdmin() {
      return userInfo.value?.role === 'admin'
    },
    subtitle() {
      return this.isAdmin
        ? '审核学生的实验室预约，或按状态、实验室查看全部预约记录'
        : '查看我的预约记录，待审核的预约可以取消'
    }
  },
  mounted() {
    this.loadLabOptions()
    this.loadList()
  },
  methods: {
    statusLabel(status) {
      return STATUS_LABELS[status] ?? '-'
    },
    statusTagType(status) {
      return STATUS_TAG_TYPES[status] ?? 'info'
    },
    // 只有预约者本人能取消，管理员也不能代取消
    isMine(row) {
      return row.user_id === userInfo.value?.id
    },

    async loadLabOptions() {
      try {
        const data = await getLabList({ page: 1, page_size: LAB_OPTIONS_PAGE_SIZE })
        this.labOptions = Array.isArray(data?.list) ? data.list : []
      } catch {
        // 错误提示由响应拦截器统一处理
      }
    },

    async loadList() {
      this.loading = true
      try {
        const data = await getReservationList({
          page: this.query.page,
          page_size: this.query.page_size,
          status: this.query.status === 'all' ? undefined : Number(this.query.status),
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
    handleSearch() {
      this.query.page = 1
      this.loadList()
    },

    // 审核（管理员）

    async handleAudit(row, status) {
      const action = status === 1 ? '同意' : '驳回'

      try {
        await ElMessageBox.confirm(
          `确定${action}「${row.nickname || row.username || '该用户'}」${row.date} ${row.start_time}-${row.end_time} 对「${row.lab_name}」的预约吗？`,
          `${action}确认`,
          { type: 'warning', confirmButtonText: `确定${action}`, cancelButtonText: '取消' }
        )
      } catch {
        return // 用户取消
      }

      try {
        await auditReservation(row.id, { status })
        ElMessage.success(`已${action}该预约`)
        await this.loadList()
      } catch {
        // 错误提示由响应拦截器统一处理
      }
    },

    // 取消（本人）

    async handleCancel(row) {
      try {
        await ElMessageBox.confirm(
          `确定取消「${row.lab_name}」${row.date} ${row.start_time}-${row.end_time} 的预约吗？`,
          '取消确认',
          { type: 'warning', confirmButtonText: '确定取消', cancelButtonText: '关闭' }
        )
      } catch {
        return // 用户取消
      }

      try {
        await cancelReservation(row.id)
        ElMessage.success('取消预约成功')
        await this.loadList()
      } catch {
        // 错误提示由响应拦截器统一处理
      }
    },

    handlePageChange(page) {
      this.query.page = page
      this.loadList()
    },
    handleSizeChange(size) {
      this.query.page_size = size
      this.query.page = 1
      this.loadList()
    }
  }
}
