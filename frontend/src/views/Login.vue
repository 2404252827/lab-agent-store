<template>
  <main class="auth-page">
    <section class="auth-card">
      <div class="auth-brand">
        <span class="auth-brand-icon" aria-hidden="true">
          <el-icon><School /></el-icon>
        </span>
        <span class="auth-brand-copy">
          <strong>智能实验室</strong>
          <small>预约管理平台</small>
        </span>
      </div>

      <header class="auth-heading">
        <h1>欢迎回来</h1>
        <p>登录后继续使用实验室预约系统</p>
      </header>

      <el-form
        ref="loginForm"
        :model="form"
        :rules="rules"
        label-position="top"
        size="large"
        @submit.prevent="submitLogin"
      >
        <el-form-item label="账号" prop="username">
          <el-input
            v-model.trim="form.username"
            placeholder="请输入账号"
            autocomplete="username"
            clearable
          />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            autocomplete="current-password"
            show-password
          />
        </el-form-item>

        <div class="auth-options">
          <el-checkbox v-model="form.remember">记住我</el-checkbox>
          <button class="auth-text-button" type="button" @click="handleForgotPassword">
            忘记密码？
          </button>
        </div>

        <el-button class="auth-submit" type="primary" native-type="submit" :loading="loading">
          登录
        </el-button>
      </el-form>

      <p class="auth-footer">
        还没有账号？
        <router-link class="auth-link" to="/register">立即注册</router-link>
      </p>
    </section>
  </main>
</template>

<script src="../scripts/login.js"></script>

<style scoped src="../assets/css/auth.css"></style>


