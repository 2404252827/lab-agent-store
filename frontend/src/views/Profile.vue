<template>
  <section class="profile-page">
    <header class="profile-heading">
      <h2 class="profile-title">个人信息</h2>
      <p class="profile-subtitle">查看并维护你的账号资料与头像</p>
    </header>

    <div class="profile-body">
      <aside class="profile-avatar">
        <img
          v-if="avatarUrl"
          class="profile-avatar__img"
          :src="avatarUrl"
          :alt="userName + '的头像'"
        />
        <span v-else class="profile-avatar__placeholder" aria-hidden="true">
          <el-icon><UserFilled /></el-icon>
        </span>

        <el-upload
          class="profile-avatar__upload"
          accept="image/*"
          :show-file-list="false"
          :disabled="uploading"
          :http-request="requestAvatarUpload"
        >
          <el-button type="primary" plain :loading="uploading">更换头像</el-button>
        </el-upload>

        <p class="profile-avatar__tip">支持 jpg / png / gif / webp，大小不超过 2MB</p>
      </aside>

      <el-form
        ref="profileForm"
        class="profile-form"
        :model="form"
        :rules="rules"
        label-position="top"
        size="large"
        @submit.prevent="submitProfile"
      >
        <el-form-item label="账号">
          <el-input :model-value="user?.username || ''" disabled />
        </el-form-item>

        <el-form-item label="角色">
          <el-input :model-value="user?.role || ''" disabled />
        </el-form-item>

        <el-form-item label="昵称" prop="nickname">
          <el-input
            v-model.trim="form.nickname"
            placeholder="请输入昵称"
            maxlength="20"
            clearable
          />
        </el-form-item>

        <el-form-item label="邮箱" prop="email">
          <el-input v-model.trim="form.email" placeholder="请输入邮箱（选填）" clearable />
        </el-form-item>

        <el-form-item label="手机号" prop="phone">
          <el-input v-model.trim="form.phone" placeholder="请输入手机号（选填）" clearable />
        </el-form-item>

        <div class="profile-actions">
          <el-button type="primary" native-type="submit" :loading="saving">
            保存修改
          </el-button>
          <el-button :disabled="saving || uploading" @click="resetForm">重置</el-button>
        </div>
      </el-form>
    </div>
  </section>
</template>

<script src="../scripts/profile.js"></script>

<style scoped src="../assets/css/profile.css"></style>
