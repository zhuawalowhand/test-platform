<template>
  <div>
    <div class="page-header">
      <h2>用例管理</h2>
      <div class="header-actions">
        <el-input
          v-model="searchQuery"
          placeholder="搜索用例名称"
          clearable
          style="width: 200px"
          prefix-icon="Search"
        />
        <el-select v-model="filterMethod" placeholder="筛选方法" clearable style="width: 120px">
          <el-option label="GET" value="GET" />
          <el-option label="POST" value="POST" />
          <el-option label="PUT" value="PUT" />
          <el-option label="DELETE" value="DELETE" />
        </el-select>
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>新建
        </el-button>
        <el-dropdown @command="handleBatchCommand">
          <el-button :disabled="selectedIds.length === 0">
            批量操作<el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="execute">批量执行</el-dropdown-item>
              <el-dropdown-item command="delete" divided>批量删除</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-dropdown @command="handleImportExport">
          <el-button>
            导入导出<el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="export">导出 JSON</el-dropdown-item>
              <el-dropdown-item command="import">导入 JSON</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <SkeletonTable :loading="loading" :rows="5" :cols="7">
      <el-table
        :data="filteredTestcases"
        border
        @selection-change="handleSelectionChange"
      >
      <el-table-column type="selection" width="50" />
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="用例名称">
        <template #default="{ row }">
          <el-link type="primary" @click="router.push(`/testcases/${row.id}`)">{{ row.name }}</el-link>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" show-overflow-tooltip />
      <el-table-column prop="method" label="方法" width="80">
        <template #default="{ row }">
          <el-tag :type="methodColor(row.method)" size="small">{{ row.method }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="url" label="URL" show-overflow-tooltip />
      <el-table-column prop="expected_status" label="预期" width="70" />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <div style="display: flex; gap: 4px; flex-wrap: nowrap;">
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" type="success" @click="handleExecuteOne(row)">执行</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </div>
        </template>
      </el-table-column>
      </el-table>
    </SkeletonTable>

    <div class="table-footer" v-if="filteredTestcases.length > 0">
      <span>共 {{ filteredTestcases.length }} 条，已选 {{ selectedIds.length }} 条</span>
      <el-button type="success" @click="handleExecuteAll" :loading="executing">
        <el-icon><VideoPlay /></el-icon>执行全部
      </el-button>
    </div>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="showDialog" :title="isEdit ? '编辑用例' : '新建用例'" width="600px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="用例名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" />
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
          <el-input v-model="form.headers" type="textarea" :rows="2" placeholder='{"Content-Type": "application/json"}' />
        </el-form-item>
        <el-form-item label="请求体">
          <el-input v-model="form.body" type="textarea" :rows="3" placeholder='{"key": "value"}' />
        </el-form-item>
        <el-form-item label="预期状态码" prop="expected_status">
          <el-input-number v-model="form.expected_status" :min="100" :max="599" />
        </el-form-item>
        <el-form-item label="标签">
          <el-input v-model="form.tags" placeholder="逗号分隔，如: smoke,regression" />
          <div class="form-tip">多个标签用逗号分隔，可用于筛选和分组</div>
        </el-form-item>
        <el-form-item label="高级断言">
          <el-input
            v-model="form.assertions"
            type="textarea"
            :rows="4"
            placeholder='[{"type":"body_contains","target":"","expected":"成功"},{"type":"response_time","target":"","expected":3000,"operator":"<"}]'
          />
          <div class="form-tip">
            JSON 数组，支持: body_contains, body_json, header, response_time, body_regex
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 隐藏的文件上传 -->
    <input
      ref="fileInput"
      type="file"
      accept=".json"
      style="display: none"
      @change="handleFileImport"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { testcaseApi, executeApi } from '../api'
import { useRouter } from 'vue-router'
import SkeletonTable from '../components/SkeletonTable.vue'

const router = useRouter()
const testcases = ref([])
const loading = ref(false)
const executing = ref(false)
const showDialog = ref(false)
const saving = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const formRef = ref()
const fileInput = ref()

const searchQuery = ref('')
const filterMethod = ref('')
const selectedIds = ref([])

const form = reactive({
  name: '',
  description: '',
  method: 'GET',
  url: '',
  headers: '{}',
  body: '{}',
  expected_status: 200,
  tags: '',
  assertions: ''
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

const filteredTestcases = computed(() => {
  return testcases.value.filter(tc => {
    const matchSearch = !searchQuery.value ||
      tc.name.toLowerCase().includes(searchQuery.value.toLowerCase())
    const matchMethod = !filterMethod.value || tc.method === filterMethod.value
    return matchSearch && matchMethod
  })
})

const loadTestcases = async () => {
  loading.value = true
  try {
    testcases.value = await testcaseApi.list()
  } finally {
    loading.value = false
  }
}

onMounted(loadTestcases)

const handleSelectionChange = (selection) => {
  selectedIds.value = selection.map(s => s.id)
}

const handleCreate = () => {
  isEdit.value = false
  editId.value = null
  Object.assign(form, {
    name: '', description: '', method: 'GET', url: '',
    headers: '{}', body: '{}', expected_status: 200,
    tags: '', assertions: ''
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
    expected_status: row.expected_status,
    tags: row.tags || '',
    assertions: row.assertions || ''
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

const handleExecuteOne = async (row) => {
  executing.value = true
  try {
    const res = await executeApi.run({ testcase_ids: [row.id], name: `执行: ${row.name}` })
    const result = res.results[0]
    if (result.passed) {
      ElMessage.success(`通过！耗时 ${result.duration_ms}ms`)
    } else {
      ElMessage.error(`失败：${result.error_message || `状态码 ${result.actual_status}`}`)
    }
  } finally {
    executing.value = false
  }
}

const handleExecuteAll = async () => {
  executing.value = true
  try {
    const res = await executeApi.run({ name: '执行全部' })
    ElMessage.success(`执行完成：通过 ${res.passed}/${res.total}`)
    router.push('/reports')
  } finally {
    executing.value = false
  }
}

const handleBatchCommand = async (command) => {
  if (selectedIds.value.length === 0) return

  if (command === 'execute') {
    executing.value = true
    try {
      const res = await executeApi.run({
        testcase_ids: selectedIds.value,
        name: `批量执行 ${selectedIds.value.length} 条`
      })
      ElMessage.success(`执行完成：通过 ${res.passed}/${res.total}`)
      router.push('/reports')
    } finally {
      executing.value = false
    }
  } else if (command === 'delete') {
    await ElMessageBox.confirm(`确定删除选中的 ${selectedIds.value.length} 条用例？`, '提示', { type: 'warning' })
    for (const id of selectedIds.value) {
      await testcaseApi.delete(id)
    }
    ElMessage.success('批量删除成功')
    loadTestcases()
  }
}

const handleImportExport = (command) => {
  if (command === 'export') {
    const data = filteredTestcases.value.map(tc => ({
      name: tc.name,
      description: tc.description,
      method: tc.method,
      url: tc.url,
      headers: tc.headers,
      body: tc.body,
      expected_status: tc.expected_status
    }))
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `testcases_${new Date().toISOString().slice(0, 10)}.json`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } else if (command === 'import') {
    fileInput.value.click()
  }
}

const handleFileImport = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  try {
    const text = await file.text()
    const data = JSON.parse(text)

    if (!Array.isArray(data)) {
      ElMessage.error('JSON 格式错误，需要数组')
      return
    }

    let successCount = 0
    for (const item of data) {
      try {
        await testcaseApi.create({
          name: item.name || '导入用例',
          description: item.description || '',
          method: item.method || 'GET',
          url: item.url || '',
          headers: item.headers || '{}',
          body: item.body || '{}',
          expected_status: item.expected_status || 200
        })
        successCount++
      } catch (e) {
        console.error('导入失败:', item, e)
      }
    }

    ElMessage.success(`成功导入 ${successCount}/${data.length} 条用例`)
    loadTestcases()
  } catch (e) {
    ElMessage.error('解析 JSON 失败')
  }

  event.target.value = ''
}
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 10px;
}

.page-header h2 {
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.table-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 15px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
}

.form-tip {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}
</style>
