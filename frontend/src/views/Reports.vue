<template>
  <div>
    <div class="page-header">
      <h2>测试报告</h2>
    </div>

    <SkeletonTable :loading="loading" :rows="5" :cols="7">
      <el-table :data="reports" border @row-click="showDetail">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="报告名称" />
      <el-table-column prop="total" label="总数" width="80" />
      <el-table-column prop="passed" label="通过" width="80">
        <template #default="{ row }">
          <span style="color: #67c23a">{{ row.passed }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="failed" label="失败" width="80">
        <template #default="{ row }">
          <span style="color: #f56c6c">{{ row.failed }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="pass_rate" label="通过率" width="100">
        <template #default="{ row }">
          <el-progress
            :percentage="row.pass_rate"
            :color="row.pass_rate === 100 ? '#67c23a' : '#409eff'"
          />
        </template>
      </el-table-column>
      <el-table-column prop="duration_ms" label="耗时(ms)" width="100" />
      <el-table-column prop="created_at" label="执行时间" width="180">
        <template #default="{ row }">
          {{ formatTime(row.created_at) }}
        </template>
      </el-table-column>
      </el-table>
    </SkeletonTable>

    <!-- 报告详情弹窗 -->
    <el-dialog v-model="showDialog" :title="reportDetail?.name" width="900px">
      <div class="report-summary" v-if="reportDetail">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-statistic title="总用例" :value="reportDetail.total" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="通过" :value="reportDetail.passed" value-style="color: #67c23a" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="失败" :value="reportDetail.failed" value-style="color: #f56c6c" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="通过率" :value="reportDetail.pass_rate" suffix="%" />
          </el-col>
        </el-row>
      </div>

      <el-table :data="reportDetail?.results" border style="margin-top: 20px">
        <el-table-column prop="testcase_id" label="用例ID" width="80" />
        <el-table-column label="结果" width="80">
          <template #default="{ row }">
            <el-tag :type="row.passed ? 'success' : 'danger'">
              {{ row.passed ? '通过' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="expected_status" label="预期" width="80" />
        <el-table-column prop="actual_status" label="实际" width="80" />
        <el-table-column prop="duration_ms" label="耗时(ms)" width="100" />
        <el-table-column prop="error_message" label="错误信息" show-overflow-tooltip />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { executeApi } from '../api'
import SkeletonTable from '../components/SkeletonTable.vue'

const reports = ref([])
const loading = ref(false)
const showDialog = ref(false)
const reportDetail = ref(null)

const formatTime = (time) => {
  return new Date(time).toLocaleString('zh-CN')
}

const loadReports = async () => {
  loading.value = true
  try {
    reports.value = await executeApi.reports()
  } finally {
    loading.value = false
  }
}

onMounted(loadReports)

const showDetail = async (row) => {
  reportDetail.value = await executeApi.reportDetail(row.id)
  showDialog.value = true
}
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
}

.report-summary {
  padding: 20px;
  background: #f5f7fa;
  border-radius: 4px;
}
</style>
