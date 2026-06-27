<template>
  <div>
    <div class="page-header">
      <h2>用例管理</h2>
      <div>
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>新建用例
        </el-button>
        <el-button type="success" @click="handleExecute">
          <el-icon><VideoPlay /></el-icon>执行全部
        </el-button>
      </div>
    </div>

    <el-table :data="testcases" v-loading="loading" border>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="用例名称" />
      <el-table-column prop="method" label="方法" width="80">
        <template #default="{ row }">
          <el-tag :type="methodColor(row.method)">{{ row.method }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="url" label="URL" show-overflow-tooltip />
      <el-table-column prop="expected_status" label="预期状态码" width="100" />
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button size="small" @click="handleEdit(row)">编辑</el-button>
          <el-button size="small" type="success" @click="handleExecuteOne(row)">执行</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="showDialog" :title="isEdit ? '编辑用例' : '新建用例'" width="600px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="用例名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" />
        </el-form-item>
        <el-form-item label="请求方法" prop="method">
          <el-select v-model="form.method">
            <el-option label="GET" value="GET" />
            <el-option label="POST" value="POST" />
            <el-option label="PUT" value="PUT" />
            <el-option label="DELETE" value="DELETE" />
          </el-select>
        </el-form-item>
        <el-form-item label="URL" prop="url">
          <el-input v-model="form.url" placeholder="https://api.example.com/endpoint" />
        </el-form-item>
        <el-form-item label="请求头">
          <el-input v-model="form.headers" type="textarea" placeholder='{"Content-Type": "application/json"}' />
        </el-form-item>
        <el-form-item label="请求体">
          <el-input v-model="form.body" type="textarea" placeholder='{"key": "value"}' />
        </el-form-item>
        <el-form-item label="预期状态码" prop="expected_status">
          <el-input-number v-model="form.expected_status" :min="100" :max="599" />
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
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { testcaseApi, executeApi } from '../api'
import { useRouter } from 'vue-router'

const router = useRouter()
const testcases = ref([])
const loading = ref(false)
const showDialog = ref(false)
const saving = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const formRef = ref()

const form = reactive({
  name: '',
  description: '',
  method: 'GET',
  url: '',
  headers: '{}',
  body: '{}',
  expected_status: 200
})

const rules = {
  name: [{ required: true, message: '请输入用例名称', trigger: 'blur' }],
  method: [{ required: true, message: '请选择请求方法', trigger: 'change' }],
  url: [{ required: true, message: '请输入URL', trigger: 'blur' }],
  expected_status: [{ required: true, message: '请输入预期状态码', trigger: 'blur' }]
}

const methodColor = (method) => {
  const colors = { GET: 'success', POST: 'primary', PUT: 'warning', DELETE: 'danger' }
  return colors[method] || 'info'
}

const loadTestcases = async () => {
  loading.value = true
  try {
    testcases.value = await testcaseApi.list()
  } finally {
    loading.value = false
  }
}

onMounted(loadTestcases)

const handleCreate = () => {
  isEdit.value = false
  editId.value = null
  Object.assign(form, {
    name: '', description: '', method: 'GET', url: '',
    headers: '{}', body: '{}', expected_status: 200
  })
  showDialog.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  editId.value = row.id
  Object.assign(form, {
    name: row.name,
    description: row.description || '',
    method: row.method,
    url: row.url,
    headers: row.headers || '{}',
    body: row.body || '{}',
    expected_status: row.expected_status
  })
  showDialog.value = true
}

const handleSave = async () => {
  await formRef.value.validate()
  saving.value = true
  try {
    if (isEdit.value) {
      await testcaseApi.update(editId.value, form)
      ElMessage.success('更新成功')
    } else {
      await testcaseApi.create(form)
      ElMessage.success('创建成功')
    }
    showDialog.value = false
    loadTestcases()
  } finally {
    saving.value = false
  }
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm('确定删除该用例？', '提示', { type: 'warning' })
  await testcaseApi.delete(row.id)
  ElMessage.success('删除成功')
  loadTestcases()
}

const handleExecute = async () => {
  loading.value = true
  try {
    const res = await executeApi.run({ name: '手动执行' })
    ElMessage.success(`执行完成：通过 ${res.passed}/${res.total}`)
    router.push('/reports')
  } finally {
    loading.value = false
  }
}

const handleExecuteOne = async (row) => {
  loading.value = true
  try {
    const res = await executeApi.run({ testcase_ids: [row.id], name: `执行: ${row.name}` })
    const result = res.results[0]
    if (result.passed) {
      ElMessage.success(`通过！耗时 ${result.duration_ms}ms`)
    } else {
      ElMessage.error(`失败：${result.error_message || `状态码 ${result.actual_status}`}`)
    }
  } finally {
    loading.value = false
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

.page-header h2 {
  margin: 0;
}
</style>
