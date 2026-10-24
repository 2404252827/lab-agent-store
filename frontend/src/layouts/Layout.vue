<template>
  <div class="common-layout">
    <div
      v-if="isMobile && mobileMenuOpen"
      class="mobile-mask"
      role="button"
      tabindex="0"
      aria-label="关闭导航菜单"
      @click="closeMobileMenu"
      @keydown.enter="closeMobileMenu"
      @keydown.space.prevent="closeMobileMenu"
    />

    <el-container class="layout-container">
      <el-aside
        class="layout-aside"
        :class="{
          'is-collapsed': isCollapsed && !isMobile,
          'is-mobile': isMobile,
          'is-mobile-open': isMobile && mobileMenuOpen
        }"
        :width="isMobile ? '240px' : asideWidth"
      >
        <div v-if="isMobile" class="drawer-header">
          <div class="drawer-brand">
            <span class="drawer-brand-icon" aria-hidden="true">
              <el-icon><School /></el-icon>
            </span>
            <span>导航菜单</span>
          </div>
          <button
            class="drawer-close"
            type="button"
            aria-label="关闭导航菜单"
            @click="closeMobileMenu"
          >
            <el-icon><Close /></el-icon>
          </button>
        </div>

        <div v-else class="menu-caption">
          <span>功能导航</span>
        </div>

        <el-menu
          class="layout-menu"
          router
          :default-active="route.path"
          :collapse="isCollapsed && !isMobile"
          :collapse-transition="false"
        >
          <el-menu-item index="/manager/home">
            <el-icon><HomeFilled /></el-icon>
            <template #title>
              <span>系统首页</span>
            </template>
          </el-menu-item>
          <el-menu-item index="/manager/ai">
            <el-icon><ChatDotRound /></el-icon>
            <template #title>
              <span>AI 智能助手</span>
            </template>
          </el-menu-item>
          <el-menu-item index="/manager/lab">
            <el-icon><Document /></el-icon>
            <template #title>
              <span>实验室管理</span>
            </template>
          </el-menu-item>
          <el-menu-item index="/manager/equipment">
            <el-icon><Box /></el-icon>
            <template #title>
              <span>设备管理</span>
            </template>
          </el-menu-item>
          <el-menu-item index="/manager/reservation">
            <el-icon><Calendar /></el-icon>
            <template #title>
              <span>预约管理</span>
            </template>
          </el-menu-item>
          <el-menu-item v-if="isAdmin" index="/manager/user">
            <el-icon><User /></el-icon>
            <template #title>
              <span>用户管理</span>
            </template>
          </el-menu-item>
        </el-menu>

        <div v-show="!isCollapsed || isMobile" class="aside-footer">
          <span class="aside-status-dot" aria-hidden="true"></span>
          <span>系统运行正常</span>
        </div>
      </el-aside>

      <el-container class="content-container">
        <el-header class="layout-header" height="64px">
          <div class="header-left">
            <button
              class="header-action header-action--desktop"
              type="button"
              :aria-label="isCollapsed ? '展开侧边栏' : '收起侧边栏'"
              :title="isCollapsed ? '展开侧边栏' : '收起侧边栏'"
              @click="toggleCollapse"
            >
              <el-icon>
                <Expand v-if="isCollapsed" />
                <Fold v-else />
              </el-icon>
            </button>

            <button
              class="header-action header-action--mobile"
              type="button"
              aria-label="打开导航菜单"
              title="打开导航菜单"
              @click="toggleMobileMenu"
            >
              <el-icon><Menu /></el-icon>
            </button>

            <div class="header-brand">
              <span class="brand-icon" aria-hidden="true">
                <el-icon><School /></el-icon>
              </span>
              <span class="brand-copy">
                <strong>智能实验室</strong>
                <small>预约管理平台</small>
              </span>
            </div>

            <span class="header-divider" aria-hidden="true"></span>

            <el-breadcrumb class="breadcrumb" separator="/">
              <el-breadcrumb-item :to="{ path: '/manager/home' }">工作台</el-breadcrumb-item>
              <el-breadcrumb-item v-if="pageTitle">{{ pageTitle }}</el-breadcrumb-item>
            </el-breadcrumb>
          </div>

          <el-dropdown class="user-dropdown" trigger="click" @command="handleCommand">
            <div class="user-info" :aria-label="`当前用户：${userName}，${userRole}`">
              <img
                v-if="avatarUrl"
                class="user-avatar user-avatar__img"
                :src="avatarUrl"
                :alt="userName + '的头像'"
              />
              <span v-else class="user-avatar" aria-hidden="true">
                <el-icon><UserFilled /></el-icon>
              </span>
              <span class="user-copy">
                <strong>{{ userName }}</strong>
                <small v-if="userRole">{{ userRole }}</small>
              </span>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人信息</el-dropdown-item>
                <el-dropdown-item command="password">修改密码</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </el-header>

        <el-main class="layout-main">
          <section class="page-panel">
            <router-view v-slot="{ Component }">
              <component :is="Component" :key="route.path" />
            </router-view>
          </section>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script src="../scripts/layout.js"></script>

<style scoped src="./Layout.css"></style>
