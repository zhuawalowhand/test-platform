<template>
  <div>
    <div class="page-header">
      <h2>定时任务</h2>
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon>新建任务
      </el-button>
    </div>

    <SkeletonTable :loading="loading" :rows="5" :cols="7">
      <el-table :data="schedules" border>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="任务名称" />
      <el-table-column prop="cron_expression" label="Cron 表达式" width="150">
        <template #default="{ row }">
          <code>{{ row.cron_expression }}</code>
        </template>
      </el-table-column>
      <el-table-column label="用例数" width="80">
        <template #default="{ row }">
          {{ countIds(row.testcase_ids) }}
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-switch
            :model-value="row.enabled"
            @change="handleToggle(row)"
            active-text="启用"
            inactive-text="禁用"
          />
        </template>
      </el-table-column>
      <el-table-column prop="last_run" label="上次执行" width="180">
        <template #default="{ row }">
          {{ row.last_run ? formatTime(row.last_run) : '从未执行' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="260">
        <template #default="{ row }">
          <el-button size="small" type="success" @click="handleRun(row)" :loading="runningId === row.id">执行</el-button>
          <el-button size="small" @click="handleEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
      </el-table>
    </SkeletonTable>

    <el-dialog v-model="showDialog" :title="isEdit ? '编辑任务' : '新建任务'" width="600px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="任务名称" prop="name">
          <el-input v-model="form.name" placeholder="如: 每日回归测试" />
        </el-form-item>
        <el-form-item label="Cron 表达式" prop="cron_expression">
          <el-input v-model="form.cron_expression" placeholder="0 0 * * *" />
          <div class="form-tip">
            格式: 分 时 日 月 周 | 例: 0 0 * * * (每天0点) | */5 * * * * (每5分钟)
          </div>
        </el-form-item>
        <el-form-item label="执行环境">
          <el-select v-model="form.environment_id" placeholder="选择环境（可选）" clearable>
            <el-option
              v-for="env in environments"
              :key="env.id"
              :label="env.name"
              :value="env.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="执行用例">
          <el-select v-model="selectedCaseIds" multiple placeholder="选择用例（不选则全部）" style="width: 100%">
            <el-option
              v-for="tc in testcases"
              :key="tc.id"
              :label="tc.name"
              :value="tc.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="Webhook">
          <div style="display: flex; gap: 8px; width: 100%">
            <el-input v-model="form.webhook_url" placeholder="钉钉/飞书/企微/Slack Webhook URL（可选）" />
            <el-button @click="handleTestWebhook" :loading="testingWebhook" :disabled="!form.webhook_url">
              测试
            </el-button>
          </div>
          <div class="form-tip">
            支持：钉钉机器人、飞书机器人、企业微信群机器人、Slack Incoming Webhooks
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { scheduleApi, environmentApi, testcaseApi } from '../api'
import SkeletonTable from '../components/SkeletonTable.vue'

const schedules = ref([])
const environments = ref([])
const testcases = ref([])
const loading = ref(false)
const showDialog = ref(false)
const saving = ref(false)
const testingWebhook = ref(false)
const runningId = ref(null)
const isEdit = ref(false)
const editId = ref(null)
const formRef = ref()
const selectedCaseIds = ref([])

const form = reactive({
  name: '',
  cron_expression: '',
  environment_id: null,
  webhook_url: ''
})

const rules = {
  name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  cron_expression: [{ required: true, message: '请输入Cron表达式', trigger: 'blur' }]
}

const countIds = (ids) => {
  try {
    const arr = JSON.parse(ids || '[]')
    return arr.length || '全部'
  } catch {
    return 0
  }
}

const formatTime = (time) => new Date(time).toLocaleString('zh-CN')

const loadSchedules = async () => {
  loading.value = true
  try {
    const [s, e, t] = await Promise.all([
      scheduleApi.list(),
      environmentApi.list(),
      testcaseApi.list()
    ])
    schedules.value = s
    environments.value = e
    testcases.value = t
  } finally {
    loading.value = false
  }
}

onMounted(loadSchedules)

const handleCreate = () => {
  isEdit.value = false
  editId.value = null
  selectedCaseIds.value = []
  Object.assign(form, { name: '', cron_expression: '', environment_id: null, webhook_url: '' })
  showDialog.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  editId.value = row.id
  selectedCaseIds.value = JSON.parse(row.testcase_ids || '[]')
  Object.assign(form, {
    name: row.name,
    cron_expression: row.cron_expression,
    environment_id: row.environment_id,
    webhook_url: row.webhook_url || ''
  })
  showDialog.value = true
}

const handleSave = async () => {
  await formRef.value.validate()
  saving.value = true
  try {
    const data = {
      ...form,
      testcase_ids: JSON.stringify(selectedCaseIds.value)
    }
    if (isEdit.value) {
      await scheduleApi.update(editId.value, data)
      ElMessage.success('更新成功')
    } else {
      await scheduleApi.create(data)
      ElMessage.success('创建成功')
    }
    showDialog.value = false
    loadSchedules()
  } finally {
    saving.value = false
  }
}

const handleToggle = async (row) => {
  await scheduleApi.toggle(row.id)
  ElMessage.success(row.enabled ? '已禁用' : '已启用')
  loadSchedules()
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm(`确定删除任务 "${row.name}"？`, '提示', { type: 'warning' })
  await scheduleApi.delete(row.id)
  ElMessage.success('删除成功')
  loadSchedules()
}

const handleRun = async (row) => {
  runningId.value = row.id
  try {
    const res = await scheduleApi.run(row.id)
    ElMessage.success(`执行完成：通过 ${res.passed}/${res.total}，通过率 ${res.pass_rate}%`)
    if (res.webhook_sent) {
      ElMessage.info('Webhook 通知已发送')
    }
    loadSchedules()
  } catch (e) {
    // error handled by interceptor
  } finally {
    runningId.value = null
  }
}

const handleTestWebhook = async () => {
  if (!form.webhook_url) {
    ElMessage.warning('请先输入 Webhook URL')
    return
  }
  testingWebhook.value = true
  try {
    const res = await executeApi.testWebhook(form.webhook_url)
    if (res.success) {
      ElMessage.success(res.message || '通知发送成功，请检查对应平台')
    } else {
      ElMessage.error(res.message || '通知发送失败')
    }
  } catch (e) {
    ElMessage.error('测试失败')
  } finally {
    testingWebhook.value = false
  }
}
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.page-header h2 { margin: 0; }
.form-tip {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}
code {
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 13px;
}
</style>
