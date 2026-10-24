<template>
  <section class="equipment-page">
    <header class="equipment-heading">
      <h2 class="equipment-title">设备管理</h2>
      <p class="equipment-subtitle">{{ subtitle }}</p>
    </header>

    <div class="equipment-toolbar">
      <div class="equipment-search">
        <el-input
          v-model.trim="query.keyword"
          class="equipment-search__input"
          placeholder="搜索设备名称"
          clearable
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <el-select
          v-model="query.lab_id"
          class="equipment-search__select"
          placeholder="全部实验室"
          clearable
          filterable
          @change="handleSearch"
        >
          <el-option v-for="lab in labOptions" :key="lab.id" :label="lab.name" :value="lab.id" />
        </el-select>

        <el-button type="primary" @click="handleSearch">搜索</el-button>
        <el-button @click="resetSearch">重置</el-button>
      </div>

      <el-button v-if="isAdmin" type="primary" @click="openCreate">新增设备</el-button>
    </div>

    <el-table v-loading="loading" :data="list" stripe>
      <el-table-column label="图片" width="88">
        <template #default="{ row }">
          <div class="equipment-cover-cell">
            <img
              v-if="row.img"
              class="equipment-cover-cell__img"
              :src="coverSrc(row.img)"
              :alt="row.name"
            />
            <el-icon v-else><Picture /></el-icon>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="name" label="设备名称" min-width="140" />
      <el-table-column label="所属实验室" min-width="140">
        <template #default="{ row }">{{ row.lab_name || '-' }}</template>
      </el-table-column>
      <el-table-column label="型号规格" min-width="130">
        <template #default="{ row }">{{ row.spec || '-' }}</template>
      </el-table-column>
      <el-table-column label="数量" width="90">
        <template #default="{ row }">{{ row.quantity ?? 0 }}</template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.status === 1 ? 'success' : 'warning'" size="small" disable-transitions>
            {{ row.status === 1 ? '正常' : '维修' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column v-if="isAdmin" label="操作" width="130">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
      <template #empty>
        <el-empty description="暂无设备数据" />
      </template>
    </el-table>

    <div class="equipment-pagination">
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
      width="520px"
      append-to-body
      :close-on-click-modal="false"
    >
      <el-form ref="equipmentForm" :model="form" :rules="rules" label-width="96px">
        <el-form-item label="所属实验室" prop="lab_id">
          <el-select
            v-model="form.lab_id"
            class="equipment-form__select"
            placeholder="请选择所属实验室"
            filterable
          >
            <el-option v-for="lab in labOptions" :key="lab.id" :label="lab.name" :value="lab.id" />
          </el-select>
        </el-form-item>

        <el-form-item label="设备名称" prop="name">
          <el-input
            v-model.trim="form.name"
            placeholder="请输入设备名称"
            maxlength="50"
            clearable
          />
        </el-form-item>

        <el-form-item label="型号规格" prop="spec">
          <el-input
            v-model.trim="form.spec"
            placeholder="选填，如：XH-2000"
            maxlength="100"
            clearable
          />
        </el-form-item>

        <el-form-item label="数量" prop="quantity">
          <el-input-number v-model="form.quantity" :min="0" :max="9999" controls-position="right" />
          <span class="equipment-quantity-suffix">台</span>
        </el-form-item>

        <el-form-item label="状态">
          <el-switch
            v-model="form.status"
            :active-value="1"
            :inactive-value="0"
            active-text="正常"
            inactive-text="维修"
          />
        </el-form-item>

        <el-form-item label="图片">
          <div class="equipment-cover-field">
            <div class="equipment-cover-preview">
              <img
                v-if="coverUrl"
                class="equipment-cover-preview__img"
                :src="coverUrl"
                alt="图片预览"
              />
              <el-icon v-else><Picture /></el-icon>
            </div>

            <div>
              <el-upload
                accept="image/*"
                :show-file-list="false"
                :disabled="uploading"
                :http-request="requestCoverUpload"
              >
                <el-button :loading="uploading">上传图片</el-button>
              </el-upload>
              <el-button v-if="coverUrl" link type="danger" @click="clearCover">移除图片</el-button>
              <p class="equipment-cover-tip">支持 jpg / png / gif / webp，不超过 2MB</p>
            </div>
          </div>
        </el-form-item>

        <el-form-item label="说明" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            maxlength="500"
            show-word-limit
            placeholder="选填"
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

<script src="../scripts/equipment.js"></script>

<style scoped src="../assets/css/equipment.css"></style>
