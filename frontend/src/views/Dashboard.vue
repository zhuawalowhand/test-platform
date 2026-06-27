<template>
  <div>
    <h2 style="margin-bottom: 20px">数据概览</h2>

    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="用例总数" :value="stats.totalCases">
            <template #prefix>
              <el-icon><Document /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="测试报告" :value="stats.totalReports">
            <template #prefix>
              <el-icon><DataAnalysis /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="平均通过率" :value="stats.avgPassRate" suffix="%">
            <template #prefix>
              <el-icon><TrendCharts /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="今日执行" :value="stats.todayExecutions">
            <template #prefix>
              <el-icon><Timer /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>最近报告</span>
          </template>
          <el-table :data="recentReports" size="small" @row-click="goReport">
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="pass_rate" label="通过率" width="100">
              <template #default="{ row }">
                <el-tag :type="row.pass_rate === 100 ? 'success' : 'warning'" size="small">
                  {{ row.pass_rate }}%
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="时间" width="160">
              <template #default="{ row }">
                {{ formatTime(row.created_at) }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card>
          <template #header>
            <span>快捷操作</span>
          </template>
          <div class="quick-actions">
            <el-button type="primary" size="large" @click="$router.push('/testcases')">
              <el-icon><Document /></el-icon>管理用例
            </el-button>
            <el-button type="success" size="large" @click="quickExecute">
              <el-icon><VideoPlay /></el-icon>快速执行
            </el-button>
            <el-button type="warning" size="large" @click="$router.push('/reports')">
              <el-icon><DataAnalysis /></el-icon>查看报告
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { testcaseApi, executeApi } from '../api'

const router = useRouter()

const stats = reactive({
  totalCases: 0,
  totalReports: 0,
  avgPassRate: 0,
  todayExecutions: 0
})

const recentReports = ref([])

const formatTime = (time) => {
  return new Date(time).toLocaleString('zh-CN')
}

const loadStats = async () => {
  try {
    const [cases, reports] = await Promise.all([
      testcaseApi.list(),
      executeApi.reports({ limit: 10 })
    ])

    stats.totalCases = cases.length
    stats.totalReports = reports.length

    if (reports.length > 0) {
      const avgRate = reports.reduce((sum, r) => sum + r.pass_rate, 0) / reports.length
      stats.avgPassRate = Math.round(avgRate)

      const today = new Date().toDateString()
      stats.todayExecutions = reports.filter(r =>
        new Date(r.created_at).toDateString() === today
      ).length
    }

    recentReports.value = reports.slice(0, 5)
  } catch (e) {
    console.error('加载统计失败:', e)
  }
}

onMounted(loadStats)

const goReport = (row) => {
  router.push('/reports')
}

const quickExecute = async () => {
  try {
    const res = await executeApi.run({ name: '快速执行' })
    ElMessage.success(`执行完成：通过 ${res.passed}/${res.total}`)
    router.push('/reports')
  } catch (e) {
    // error handled by interceptor
  }
}
</script>

<style scoped>
.stats-row .el-card {
  text-align: center;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.quick-actions .el-button {
  width: 100%;
}
</style>
