<template>
  <div>
    <el-page-header @back="router.back()" style="margin-bottom: 20px">
      <template #content>
        <span style="font-size: 18px; font-weight: 600">{{ testcase?.name || '用例详情' }}</span>
      </template>
    </el-page-header>

    <el-row :gutter="20">
      <!-- 用例基本信息 -->
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>用例信息</span>
          </template>
          <el-descriptions :column="1" border v-if="testcase">
            <el-descriptions-item label="ID">{{ testcase.id }}</el-descriptions-item>
            <el-descriptions-item label="名称">{{ testcase.name }}</el-descriptions-item>
            <el-descriptions-item label="方法">
              <el-tag :type="methodColor(testcase.method)" size="small">{{ testcase.method }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="URL">{{ testcase.url }}</el-descriptions-item>
            <el-descriptions-item label="预期状态码">{{ testcase.expected_status }}</el-descriptions-item>
            <el-descriptions-item label="标签">
              <el-tag v-for="tag in tags" :key="tag" size="small" style="margin-right: 4px">{{ tag }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="描述">{{ testcase.description || '-' }}</el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ formatTime(testcase.created_at) }}</el-descriptions-item>
            <el-descriptions-item label="更新时间">{{ testcase.updated_at ? formatTime(testcase.updated_at) : '-' }}</el-descriptions-item>
          </el-descriptions>

          <el-button type="success" style="width: 100%; margin-top: 15px" @click="handleExecute" :loading="executing">
            <el-icon><VideoPlay /></el-icon>执行此用例
          </el-button>
        </el-card>

        <!-- 断言规则 -->
        <el-card style="margin-top: 20px" v-if="assertions.length > 0">
          <template #header>
            <span>断言规则</span>
          </template>
          <el-table :data="assertions" size="small" border>
            <el-table-column prop="type" label="类型" width="120" />
            <el-table-column prop="target" label="目标" />
            <el-table-column prop="expected" label="预期值" />
            <el-table-column prop="operator" label="操作符" width="80" v-if="assertions.some(a => a.operator)" />
          </el-table>
        </el-card>
      </el-col>

      <!-- 执行历史 -->
      <el-col :span="16">
        <el-card>
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span>执行历史</span>
              <el-input v-model="searchHistory" placeholder="搜索报告名称" clearable style="width: 200px" />
            </div>
          </template>

          <el-table :data="filteredHistory" v-loading="loading" border>
            <el-table-column label="结果" width="80">
              <template #default="{ row }">
                <el-tag :type="row.passed ? 'success' : 'danger'" size="small">
                  {{ row.passed ? '通过' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="报告" show-overflow-tooltip>
              <template #default="{ row }">
                <el-link type="primary" @click="goReport(row.report_id)">{{ row.report_name || '-' }}</el-link>
              </template>
            </el-table-column>
            <el-table-column prop="actual_status" label="实际状态" width="90">
              <template #default="{ row }">
                {{ row.actual_status ?? '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="expected_status" label="预期状态" width="90" />
            <el-table-column prop="duration_ms" label="耗时(ms)" width="90" />
            <el-table-column prop="executed_at" label="执行时间" width="180">
              <template #default="{ row }">
                {{ formatTime(row.executed_at) }}
              </template>
            </el-table-column>
            <el-table-column label="错误信息" show-overflow-tooltip>
              <template #default="{ row }">
                {{ row.error_message || '-' }}
              </template>
            </el-table-column>
          </el-table>

          <el-empty v-if="!loading && filteredHistory.length === 0" description="暂无执行记录" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { testcaseApi, executeApi } from '../api'

const route = useRoute()
const router = useRouter()

const testcase = ref(null)
const loading = ref(false)
const executing = ref(false)
const searchHistory = ref('')
const history = ref([])

const caseId = Number(route.params.id)

const tags = computed(() => {
  if (!testcase.value?.tags) return []
  return testcase.value.tags.split(',').map(t => t.trim()).filter(Boolean)
})

const assertions = computed(() => {
  if (!testcase.value?.assertions) return []
  try {
    return JSON.parse(testcase.value.assertions)
  } catch {
    return []
  }
})

const filteredHistory = computed(() => {
  if (!searchHistory.value) return history.value
  return history.value.filter(h =>
    (h.report_name || '').toLowerCase().includes(searchHistory.value.toLowerCase())
  )
})

const methodColor = (method) => {
  const colors = { GET: 'success', POST: 'primary', PUT: 'warning', DELETE: 'danger' }
  return colors[method] || 'info'
}

const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const loadData = async () => {
  loading.value = true
  try {
    testcase.value = await testcaseApi.get(caseId)
    // 加载最近报告，筛选包含该用例的
    const reports = await executeApi.reports({ limit: 50 })
    const results = []
    for (const report of reports) {
      const detail = await executeApi.reportDetail(report.id)
      const match = detail.results.find(r => r.testcase_id === caseId)
      if (match) {
        results.push({
          ...match,
          report_id: report.id,
          report_name: report.name,
          passed: match.passed,
          executed_at: match.executed_at
        })
      }
    }
    history.value = results
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadData)

const handleExecute = async () => {
  executing.value = true
  try {
    const res = await executeApi.run({ testcase_ids: [caseId], name: `执行: ${testcase.value.name}` })
    const result = res.results[0]
    if (result.passed) {
      ElMessage.success(`通过！耗时 ${result.duration_ms}ms`)
    } else {
      ElMessage.error(`失败：${result.error_message || `状态码 ${result.actual_status}`}`)
    }
    loadData()
  } finally {
    executing.value = false
  }
}

const goReport = (reportId) => {
  router.push('/reports')
}
</script>
