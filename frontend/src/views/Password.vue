<template>
  <section class="password-page">
    <header class="password-heading">
      <h2 class="password-title">修改密码</h2>
      <p class="password-subtitle">定期更换密码可以提升账号安全性</p>
    </header>

    <el-form
      ref="passwordForm"
      class="password-form"
      :model="form"
      :rules="rules"
      label-position="top"
      size="large"
      @submit.prevent="submitPassword"
    >
      <el-form-item label="原密码" prop="oldPassword">
        <el-input
          v-model="form.oldPassword"
          type="password"
          placeholder="请输入原密码"
          autocomplete="current-password"
          show-password
        />
      </el-form-item>

      <el-form-item label="新密码" prop="newPassword">
        <el-input
          v-model="form.newPassword"
          type="password"
          placeholder="请输入新密码（至少 6 位）"
          autocomplete="new-password"
          show-password
        />
      </el-form-item>

      <el-form-item label="确认新密码" prop="confirmPassword">
        <el-input
          v-model="form.confirmPassword"
          type="password"
          placeholder="请再次输入新密码"
          autocomplete="new-password"
          show-password
        />
      </el-form-item>

      <div class="password-actions">
        <el-button type="primary" native-type="submit" :loading="saving">
          确认修改
        </el-button>
        <el-button :disabled="saving" @click="resetForm">重置</el-button>
      </div>
    </el-form>
  </section>
</template>

<script src="../scripts/password.js"></script>

<style scoped src="../assets/css/password.css"></style>