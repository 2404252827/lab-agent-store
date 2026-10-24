<template>
  <main class="auth-page">
    <section class="auth-card auth-card--register">
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
        <h1>创建账号</h1>
        <p>填写基本信息，快速加入实验室预约系统</p>
      </header>

      <el-form
        ref="registerForm"
        :model="form"
        :rules="rules"
        label-position="top"
        size="large"
        @submit.prevent="submitRegister"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model.trim="form.username"
            placeholder="请输入用户名"
            autocomplete="username"
            clearable
          />
        </el-form-item>

        <el-form-item label="手机号" prop="phone">
          <el-input
            v-model.trim="form.phone"
            placeholder="请输入手机号"
            autocomplete="tel"
            clearable
          />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请设置至少 6 位密码"
            autocomplete="new-password"
            show-password
          />
        </el-form-item>

        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            autocomplete="new-password"
            show-password
          />
        </el-form-item>

        <el-button class="auth-submit" type="primary" native-type="submit" :loading="loading">
          注册
        </el-button>
      </el-form>

      <p class="auth-footer">
        已有账号？
        <router-link class="auth-link" to="/login">返回登录</router-link>
      </p>
    </section>
  </main>
</template>

<script src="../scripts/register.js"></script>

<style scoped src="../assets/css/auth.css"></style>
