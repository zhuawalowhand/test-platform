<template>
  <div>
    <h2 style="margin-bottom: 20px">个人设置</h2>

    <el-card>
      <template #header>
        <span>账号信息</span>
      </template>

      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px" style="max-width: 500px">
        <el-form-item label="用户名">
          <el-input :value="user.username" disabled />
        </el-form-item>

        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" />
        </el-form-item>

        <el-form-item label="新密码">
          <el-input v-model="form.password" type="password" placeholder="留空则不修改" show-password />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card style="margin-top: 20px">
      <template #header>
        <span>主题设置</span>
      </template>
      <div style="display: flex; gap: 20px; align-items: center">
        <span>当前主题：{{ isDark ? '深色' : '浅色' }}</span>
        <el-button @click="toggleTheme">切换主题</el-button>
      </div>
    </el-card>

    <el-card style="margin-top: 20px">
      <template #header>
        <span>关于平台</span>
      </template>
      <div>
        <p><strong>接口测试平台</strong> v0.2.0</p>
        <p>技术栈：Vue 3 + Element Plus + FastAPI + PostgreSQL</p>
        <p>支持功能：用例管理、执行测试、测试报告、环境配置、定时任务</p>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { userApi } from '../api'
import { useTheme } from '../composables/useTheme'

const formRef = ref()
const saving = ref(false)
const user = ref({})
const { isDark, toggleTheme } = useTheme()

const form = reactive({
  email: '',
  password: ''
})

const rules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效邮箱', trigger: 'blur' }
  ]
}

onMounted(async () => {
  try {
    user.value = await userApi.getMe()
    form.email = user.value.email
  } catch (e) {
    console.error('获取用户信息失败:', e)
  }
})

const handleSave = async () => {
  await formRef.value.validate()
  saving.value = true
  try {
    const data = { email: form.email }
    if (form.password) {
      data.password = form.password
    }
    await userApi.update(data)
    ElMessage.success('保存成功')
    user.value.email = form.email
    form.password = ''
  } finally {
    saving.value = false
  }
}

const handleReset = () => {
  form.email = user.value.email
  form.password = ''
}
</script>
