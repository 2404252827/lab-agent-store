<template>
  <section class="user-page">
    <header class="user-heading">
      <h2 class="user-title">用户管理</h2>
      <p class="user-subtitle">维护系统内的学生账号，支持新增、编辑与删除</p>
    </header>

    <div class="user-toolbar">
      <div class="user-search">
        <el-input
          v-model.trim="query.keyword"
          class="user-search__input"
          placeholder="搜索账号或昵称"
          clearable
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="handleSearch">搜索</el-button>
        <el-button @click="resetSearch">重置</el-button>
      </div>

      <el-button type="primary" @click="openCreate">新增用户</el-button>
    </div>

    <el-table v-loading="loading" :data="list" stripe>
      <el-table-column prop="username" label="账号" min-width="120" />
      <el-table-column prop="nickname" label="昵称" min-width="120" />
      <el-table-column label="角色" min-width="90">
        <template #default="{ row }">{{ roleLabel(row.role) }}</template>
      </el-table-column>
      <el-table-column label="邮箱" min-width="180">
        <template #default="{ row }">{{ row.email || '-' }}</template>
      </el-table-column>
      <el-table-column label="手机号" min-width="130">
        <template #default="{ row }">{{ row.phone || '-' }}</template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small" disable-transitions>
            {{ row.status === 1 ? '正常' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="130">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
      <template #empty>
        <el-empty description="暂无用户数据" />
      </template>
    </el-table>

    <div class="user-pagination">
      <el-pagination
        :current-page="query.page"
        :page-size="query.page_size"
        :page-sizes="[10, 20, 50]"
        :total="total"
        layout="total, sizes, prev, pager, next"
        background
        @current-change="handlePageChange"
        @size-change="handleSizeChange"
      />
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="460px"
      append-to-body
      :close-on-click-modal="false"
    >
      <el-form ref="userForm" :model="form" :rules="rules" label-width="76px">
        <el-form-item v-if="!isEdit" label="账号" prop="username">
          <el-input v-model.trim="form.username" placeholder="请输入账号" clearable />
        </el-form-item>

        <el-form-item v-if="!isEdit" label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入初始密码"
            show-password
          />
        </el-form-item>

        <el-form-item label="昵称" prop="nickname">
          <el-input v-model.trim="form.nickname" placeholder="请输入昵称" clearable />
        </el-form-item>

        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" placeholder="请选择角色">
            <el-option
              v-for="item in roleOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="邮箱" prop="email">
          <el-input v-model.trim="form.email" placeholder="选填" clearable />
        </el-form-item>

        <el-form-item label="手机号" prop="phone">
          <el-input v-model.trim="form.phone" placeholder="选填" clearable />
        </el-form-item>

        <el-form-item label="头像">
          <div class="user-avatar-field">
            <img v-if="avatarUrl" class="user-avatar-preview" :src="avatarUrl" alt="头像预览" />
            <span v-else class="user-avatar-placeholder" aria-hidden="true">
              <el-icon><UserFilled /></el-icon>
            </span>

            <div>
              <el-upload
                accept="image/*"
                :show-file-list="false"
                :disabled="uploading"
                :http-request="requestAvatarUpload"
              >
                <el-button :loading="uploading">上传头像</el-button>
              </el-upload>
              <el-button v-if="avatarUrl" link type="danger" @click="clearAvatar">
                移除头像
              </el-button>
              <p class="user-avatar-tip">支持 jpg / png / gif / webp，不超过 2MB</p>
            </div>
          </div>
        </el-form-item>

        <el-form-item label="状态">
          <el-switch
            v-model="form.status"
            :active-value="1"
            :inactive-value="0"
            active-text="正常"
            inactive-text="禁用"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button :disabled="saving" @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitForm">
          {{ isEdit ? '保存' : '新增' }}
        </el-button>
      </template>
    </el-dialog>
  </section>
</template>

<script src="../scripts/user.js"></script>

<style scoped src="../assets/css/user.css"></style>
