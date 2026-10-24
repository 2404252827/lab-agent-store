<template>
  <section class="ai-page">
    <header class="ai-heading">
      <div>
        <h2 class="ai-title">AI 智能助手</h2>
        <p class="ai-subtitle">基于实验室知识库回答，可以问我实验室、设备、预约相关的问题</p>
      </div>
      <el-button :disabled="sending || !messages.length" @click="handleClear">
        清空对话
      </el-button>
    </header>

    <div class="ai-body">
      <div class="ai-scroll">
        <div
          ref="scrollRef"
          class="ai-messages"
          :class="{ 'ai-messages--empty': !historyLoading && !messages.length && !sending }"
          @scroll="handleScroll"
        >
          <!-- 正在从服务端加载历史 -->
          <div v-if="historyLoading" class="ai-empty">
            <h3 class="ai-empty__title">正在加载对话记录…</h3>
          </div>

          <!-- 空状态：直接给几个知识库里确实能答上来的问题，降低上手成本 -->
          <div v-else-if="!messages.length" class="ai-empty">
            <span class="ai-empty__icon" aria-hidden="true">
              <el-icon><ChatDotRound /></el-icon>
            </span>
            <h3 class="ai-empty__title">你好，我能帮你快速了解这个系统</h3>
            <p class="ai-empty__desc">你可以试着问我这些问题：</p>

            <div class="ai-suggestions">
              <button
                v-for="item in suggestions"
                :key="item"
                class="ai-suggestion"
                type="button"
                @click="askSuggestion(item)"
              >
                {{ item }}
              </button>
            </div>
          </div>

          <!-- 对话记录 -->
          <div
            v-for="(message, index) in messages"
            :key="index"
            class="ai-row"
            :class="`ai-row--${message.role}`"
          >
            <span class="ai-avatar" aria-hidden="true">
              <el-icon>
                <ChatDotRound v-if="message.role === 'assistant'" />
                <UserFilled v-else />
              </el-icon>
            </span>
            <div class="ai-bubble" :class="{ 'ai-bubble--error': message.error }">
              {{ message.content }}
            </div>
          </div>

          <!-- 正在流式输出的回答 -->
          <div v-if="liveReply" class="ai-row ai-row--assistant">
            <span class="ai-avatar" aria-hidden="true">
              <el-icon><ChatDotRound /></el-icon>
            </span>
            <div class="ai-bubble">
              <!-- 正在调用工具：比空白更能说明系统在干活 -->
              <span v-if="liveReply.toolName" class="ai-tool-hint">
                {{ liveReply.toolName }}…
              </span>

              <!-- 还没有任何内容：打字动画 -->
              <span v-else-if="!liveReply.content" class="ai-typing" aria-label="正在思考">
                <span class="ai-dot" />
                <span class="ai-dot" />
                <span class="ai-dot" />
              </span>

              <!-- 流式正文 + 末尾闪烁的光标 -->
              <template v-else>
                {{ liveReply.content }}<span class="ai-caret" aria-hidden="true" />
              </template>
            </div>
          </div>
        </div>

        <!-- 用户往上翻历史时出现，点一下回到最新消息 -->
        <button
          v-show="showJump"
          class="ai-jump"
          type="button"
          aria-label="回到最新消息"
          @click="scrollToBottom(true)"
        >
          <el-icon><ArrowDown /></el-icon>
        </button>
      </div>

      <footer class="ai-input">
        <el-input
          v-model="draft"
          class="ai-input__field"
          type="textarea"
          :autosize="{ minRows: 2, maxRows: 5 }"
          resize="none"
          maxlength="2000"
          show-word-limit
          :disabled="sending"
          placeholder="请输入你的问题，Enter 发送，Shift + Enter 换行"
          @keydown="handleKeydown"
        />
        <el-button
          class="ai-input__send"
          type="primary"
          :loading="sending"
          :disabled="!canSend"
          @click="handleSend"
        >
          发送
        </el-button>
      </footer>
    </div>
  </section>
</template>

<script src="../scripts/ai.js"></script>

<style scoped src="../assets/css/ai.css"></style>
