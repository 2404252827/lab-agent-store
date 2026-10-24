<template>
  <section class="lab-page">
    <header class="lab-heading">
      <h2 class="lab-title">实验室管理</h2>
      <p class="lab-subtitle">{{ subtitle }}</p>
    </header>

    <div class="lab-toolbar">
      <div class="lab-search">
        <el-input
          v-model.trim="query.keyword"
          class="lab-search__input"
          placeholder="搜索实验室名称"
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

      <el-button v-if="isAdmin" type="primary" @click="openCreate">新增实验室</el-button>
    </div>

    <el-table v-loading="loading" :data="list" stripe>
      <el-table-column label="封面" width="88">
        <template #default="{ row }">
          <div class="lab-cover-cell">
            <img
              v-if="row.img"
              class="lab-cover-cell__img"
              :src="coverSrc(row.img)"
              :alt="row.name"
            />
            <el-icon v-else><Picture /></el-icon>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="name" label="名称" min-width="140" />
      <el-table-column prop="location" label="位置" min-width="140" />
      <el-table-column label="容量" width="100">
        <template #default="{ row }">{{ row.capacity }} 人</template>
      </el-table-column>
      <el-table-column label="开放时间" min-width="150">
        <template #default="{ row }">{{ timeRange(row) }}</template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small" disable-transitions>
            {{ row.status === 1 ? '开放' : '关闭' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="预约" width="90">
        <template #default="{ row }">
          <el-tooltip
            :disabled="row.status === 1"
            content="实验室已关闭，暂不可预约"
            placement="top"
          >
            <span class="lab-reserve-wrapper">
              <el-button
                link
                type="primary"
                :disabled="row.status !== 1"
                @click="openReservation(row)"
              >
                预约
              </el-button>
            </span>
          </el-tooltip>
        </template>
      </el-table-column>
      <el-table-column v-if="isAdmin" label="操作" width="130">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
      <template #empty>
        <el-empty description="暂无实验室数据" />
      </template>
    </el-table>

    <div class="lab-pagination">
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
      <el-form ref="labForm" :model="form" :rules="rules" label-width="88px">
        <el-form-item label="名称" prop="name">
          <el-input
            v-model.trim="form.name"
            placeholder="请输入实验室名称"
            maxlength="50"
            clearable
          />
        </el-form-item>

        <el-form-item label="位置" prop="location">
          <el-input
            v-model.trim="form.location"
            placeholder="如：实验楼 A101"
            maxlength="100"
            clearable
          />
        </el-form-item>

        <el-form-item label="容量" prop="capacity">
          <el-input-number v-model="form.capacity" :min="0" :max="9999" controls-position="right" />
          <span class="lab-capacity-suffix">人</span>
        </el-form-item>

        <el-form-item label="开放时间" prop="open_time">
          <el-time-select
            v-model="form.open_time"
            start="00:00"
            step="00:30"
            end="23:30"
            placeholder="选择开放时间"
          />
        </el-form-item>

        <el-form-item label="结束时间" prop="close_time">
          <el-time-select
            v-model="form.close_time"
            start="00:00"
            step="00:30"
            end="23:30"
            placeholder="选择结束时间"
          />
        </el-form-item>

        <el-form-item label="状态">
          <el-switch
            v-model="form.status"
            :active-value="1"
            :inactive-value="0"
            active-text="开放"
            inactive-text="关闭"
          />
        </el-form-item>

        <el-form-item label="封面">
          <div class="lab-cover-field">
            <div class="lab-cover-preview">
              <img v-if="coverUrl" class="lab-cover-preview__img" :src="coverUrl" alt="封面预览" />
              <el-icon v-else><Picture /></el-icon>
            </div>

            <div>
              <el-upload
                accept="image/*"
                :show-file-list="false"
                :disabled="uploading"
                :http-request="requestCoverUpload"
              >
                <el-button :loading="uploading">上传封面</el-button>
              </el-upload>
              <el-button v-if="coverUrl" link type="danger" @click="clearCover">移除封面</el-button>
              <p class="lab-cover-tip">支持 jpg / png / gif / webp，不超过 2MB</p>
            </div>
          </div>
        </el-form-item>

        <el-form-item label="简介" prop="description">
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

    <el-dialog
      v-model="reserveVisible"
      title="预约实验室"
      width="480px"
      append-to-body
      :close-on-click-modal="false"
    >
      <el-form ref="reserveForm" :model="reserveForm" :rules="reserveRules" label-width="88px">
        <el-form-item label="实验室">
          <span class="reserve-lab">{{ reserveForm.lab_name }}</span>
          <span class="reserve-location">{{ reserveForm.lab_location }}</span>
        </el-form-item>

        <el-form-item label="开放时间">
          <span class="reserve-open">{{ reserveTimeRange }}</span>
        </el-form-item>

        <el-form-item label="预约日期" prop="date">
          <el-date-picker
            v-model="reserveForm.date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择预约日期"
            popper-class="reservation-date-popper"
            :disabled-date="disabledReserveDate"
            :cell-class-name="reserveCellClass"
          />
        </el-form-item>

        <el-form-item label="开始时间" prop="start_time">
          <el-time-select
            v-model="reserveForm.start_time"
            :start="reserveStartTime"
            :end="reserveEndTime"
            step="00:30"
            placeholder="选择开始时间"
          />
        </el-form-item>

        <el-form-item label="结束时间" prop="end_time">
          <el-time-select
            v-model="reserveForm.end_time"
            :start="reserveForm.start_time || reserveStartTime"
            :end="reserveEndTime"
            step="00:30"
            placeholder="选择结束时间"
          />
        </el-form-item>

        <el-form-item label="备注" prop="remark">
          <el-input
            v-model="reserveForm.remark"
            type="textarea"
            :rows="3"
            maxlength="255"
            show-word-limit
            placeholder="选填"
          />
        </el-form-item>
      </el-form>

      <p class="reserve-tip">
        日期面板中标红的日期表示当天已有生效中的预约（仍可选择）；同一时间段只能被预约一次。
      </p>

      <template #footer>
        <el-button :disabled="reserving" @click="reserveVisible = false">取消</el-button>
        <el-button type="primary" :loading="reserving" @click="submitReservation">
          提交预约
        </el-button>
      </template>
    </el-dialog>
  </section>
</template>

<script src="../scripts/lab.js"></script>

<style scoped src="../assets/css/lab.css"></style>
