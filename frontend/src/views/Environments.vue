<template>
  <div>
    <div class="page-header">
      <h2>环境管理</h2>
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon>新建环境
      </el-button>
    </div>

    <el-table :data="environments" v-loading="loading" border>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="环境名称" width="150" />
      <el-table-column prop="base_url" label="基础 URL" />
      <el-table-column label="变量数" width="100">
        <template #default="{ row }">
          {{ countVariables(row.variables) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button size="small" @click="handleEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showDialog" :title="isEdit ? '编辑环境' : '新建环境'" width="600px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="环境名称" prop="name">
          <el-input v-model="form.name" placeholder="如: dev, staging, prod" />
        </el-form-item>
        <el-form-item label="基础 URL" prop="base_url">
          <el-input v-model="form.base_url" placeholder="https://api.example.com" />
        </el-form-item>
        <el-form-item label="环境变量">
          <el-input
            v-model="form.variables"
            type="textarea"
            :rows="6"
            placeholder='{"token": "xxx", "user_id": "123"}'
          />
          <div class="form-tip">JSON 格式，用例中用 &#123;&#123;变量名&#125;&#125; 引用</div>
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
import { environmentApi } from '../api'

const environments = ref([])
const loading = ref(false)
const showDialog = ref(false)
const saving = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const formRef = ref()

const form = reactive({
  name: '',
  base_url: '',
  variables: '{}'
})

const rules = {
  name: [{ required: true, message: '请输入环境名称', trigger: 'blur' }],
  base_url: [{ required: true, message: '请输入基础URL', trigger: 'blur' }]
}

const countVariables = (vars) => {
  try {
    return Object.keys(JSON.parse(vars || '{}')).length
  } catch {
    return 0
  }
}

const loadEnvironments = async () => {
  loading.value = true
  try {
    environments.value = await environmentApi.list()
  } finally {
    loading.value = false
  }
}

onMounted(loadEnvironments)

const handleCreate = () => {
  isEdit.value = false
  editId.value = null
  Object.assign(form, { name: '', base_url: '', variables: '{}' })
  showDialog.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  editId.value = row.id
  Object.assign(form, {
    name: row.name,
    base_url: row.base_url,
    variables: row.variables || '{}'
  })
  showDialog.value = true
}

const handleSave = async () => {
  await formRef.value.validate()
  // 验证 JSON
  try {
    JSON.parse(form.variables)
  } catch {
    ElMessage.error('变量必须是有效的 JSON')
    return
  }

  saving.value = true
  try {
    if (isEdit.value) {
      await environmentApi.update(editId.value, form)
      ElMessage.success('更新成功')
    } else {
      await environmentApi.create(form)
      ElMessage.success('创建成功')
    }
    showDialog.value = false
    loadEnvironments()
  } finally {
    saving.value = false
  }
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm(`确定删除环境 "${row.name}"？`, '提示', { type: 'warning' })
  await environmentApi.delete(row.id)
  ElMessage.success('删除成功')
  loadEnvironments()
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
</style>
