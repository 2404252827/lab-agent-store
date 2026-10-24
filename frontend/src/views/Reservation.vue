<template>
  <section class="reservation-page">
    <header class="reservation-heading">
      <h2 class="reservation-title">预约管理</h2>
      <p class="reservation-subtitle">{{ subtitle }}</p>
    </header>

    <div class="reservation-toolbar">
      <el-tabs v-model="query.status" class="reservation-tabs" @tab-change="handleSearch">
        <el-tab-pane
          v-for="tab in statusTabs"
          :key="tab.value"
          :label="tab.label"
          :name="tab.value"
        />
      </el-tabs>

      <el-select
        v-model="query.lab_id"
        class="reservation-search__select"
        placeholder="全部实验室"
        clearable
        filterable
        @change="handleSearch"
      >
        <el-option v-for="lab in labOptions" :key="lab.id" :label="lab.name" :value="lab.id" />
      </el-select>
    </div>

    <el-table v-loading="loading" :data="list" stripe>
      <el-table-column prop="lab_name" label="实验室" min-width="140" />
      <el-table-column v-if="isAdmin" label="预约人" min-width="120">
        <template #default="{ row }">{{ row.nickname || row.username || '-' }}</template>
      </el-table-column>
      <el-table-column prop="date" label="预约日期" width="120" />
      <el-table-column label="时间段" width="140">
        <template #default="{ row }">{{ row.start_time }} - {{ row.end_time }}</template>
      </el-table-column>
      <el-table-column label="备注" min-width="140">
        <template #default="{ row }">{{ row.remark || '-' }}</template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)" size="small" disable-transitions>
            {{ statusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="140">
        <template #default="{ row }">
          <template v-if="row.status === 0">
            <template v-if="isAdmin">
              <el-button link type="success" @click="handleAudit(row, 1)">同意</el-button>
              <el-button link type="danger" @click="handleAudit(row, 2)">驳回</el-button>
            </template>
            <el-button v-if="isMine(row)" link type="warning" @click="handleCancel(row)">
              取消
            </el-button>
          </template>
          <span v-else class="reservation-noop">-</span>
        </template>
      </el-table-column>
      <template #empty>
        <el-empty description="暂无预约数据" />
      </template>
    </el-table>

    <div class="reservation-pagination">
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
  </section>
</template>

<script src="../scripts/reservation.js"></script>

<style scoped src="../assets/css/reservation.css"></style>
