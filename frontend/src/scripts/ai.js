import { computed, nextTick, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  clearChatHistory,
  getChatHistory,
  streamChatWithAi,
  TOOL_LABELS,
} from '@/api/ai'

// 空状态里的示例问题，都是知识库里确实有答案的
const SUGGESTIONS = [
  '为什么不能预约今天？',
  '能取消已经同意的预约吗？',
  '删除实验室需要什么条件？',
  '怎么知道设备在不在维修？',
]

export default {
  setup() {
    // 对话历史完全来自服务端：后端按 JWT 里的 user_id 隔离，
    // 前端不再用 sessionStorage 缓存，避免换用户后串数据
    const messages = ref([])
    const draft = ref('')
    const sending = ref(false)
    const historyLoading = ref(true)
    const scrollRef = ref(null)
    const showJump = ref(false)

    // 正在流式输出的那条回答。
    // 单独放一个 ref，避免每收到一个 token 就触发整个列表 diff。
    const liveReply = ref(null)

    const canSend = computed(
      () =>
        !historyLoading.value &&
        draft.value.trim().length > 0 &&
        !sending.value,
    )

    // 滚到最新消息。必须等 nextTick，否则新消息还没渲染进 DOM，高度是旧的
    function scrollToBottom(smooth = false) {
      nextTick(() => {
        const el = scrollRef.value
        if (!el) return
        el.scrollTo({ top: el.scrollHeight, behavior: smooth ? 'smooth' : 'auto' })
      })
    }

    // 用户手动往上翻历史时，把「回到最新」按钮亮出来
    function handleScroll() {
      const el = scrollRef.value
      if (!el) return
      showJump.value = el.scrollHeight - el.scrollTop - el.clientHeight > 120
    }

    // 进入页面时从服务端拉取当前用户的对话历史
    async function loadHistory() {
      historyLoading.value = true

      try {
        const data = await getChatHistory()
        messages.value = (data?.messages || []).map((item) => ({
          role: item.role,
          content: item.content,
        }))
      } catch {
        // 具体原因由 request.js 的响应拦截器统一提示
        messages.value = []
      } finally {
        historyLoading.value = false
        scrollToBottom()
      }
    }

    async function handleSend() {
      const content = draft.value.trim()

      // 空内容、历史还没加载完、或正在等待回答时直接忽略
      if (!content || sending.value || historyLoading.value) return

      messages.value.push({ role: 'user', content })
      draft.value = ''
      sending.value = true
      showJump.value = false
      liveReply.value = { content: '', toolName: '' }
      scrollToBottom(true)

      try {
        await streamChatWithAi(content, {
          onTool(name) {
            if (!liveReply.value) return
            liveReply.value.toolName = TOOL_LABELS[name] || '正在处理'
            scrollToBottom()
          },
          onToken(text) {
            if (!liveReply.value) return
            // 第一个 token 到了就把「正在查询…」提示清掉
            liveReply.value.toolName = ''
            liveReply.value.content += text
            scrollToBottom()
          },
        })

        // 流正常结束，后端已经把这一问一答写入数据库
        messages.value.push({
          role: 'assistant',
          content: liveReply.value?.content || '',
        })
      } catch {
        // 具体原因（401、超时、模型报错）由 api 层处理/抛出。
        // 失败时后端不会落库，本地只留一条提示，刷新后自然消失
        const partial = liveReply.value?.content || ''

        messages.value.push(
          partial
            ? {
                role: 'assistant',
                content: `${partial}\n\n（回答中断，请重试）`,
                error: true,
              }
            : {
                role: 'assistant',
                content: '这个问题我没能回答成功，请稍后重试。',
                error: true,
              },
        )
      } finally {
        liveReply.value = null
        sending.value = false
        scrollToBottom(true)
      }
    }

    function handleKeydown(event) {
      // 中文输入法选词时按回车也会触发 keydown。
      // 不挡掉的话，用拼音选字时的回车会直接被当成「发送」
      if (event.isComposing || event.keyCode === 229) return

      // Enter 发送，Shift + Enter 换行
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault()
        handleSend()
      }
    }

    // 点示例问题：填进输入框后立刻发送
    function askSuggestion(question) {
      draft.value = question
      handleSend()
    }

    async function handleClear() {
      try {
        await ElMessageBox.confirm('确定清空当前对话吗？', '清空对话', {
          type: 'warning',
          confirmButtonText: '清空',
          cancelButtonText: '取消',
        })
      } catch {
        return // 用户点了取消
      }

      try {
        // 先删服务端，成功了再清本地；失败时界面保持原样
        await clearChatHistory()
        messages.value = []
        showJump.value = false
        ElMessage.success('已清空对话')
      } catch {
        // 具体原因由 request.js 的响应拦截器统一提示
      }
    }

    onMounted(loadHistory)

    return {
      messages,
      draft,
      sending,
      historyLoading,
      liveReply,
      scrollRef,
      showJump,
      suggestions: SUGGESTIONS,
      canSend,
      handleSend,
      handleKeydown,
      handleScroll,
      scrollToBottom,
      askSuggestion,
      handleClear,
    }
  },
}