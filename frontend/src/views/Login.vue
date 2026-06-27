<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <h2>接口测试平台</h2>
      </template>

      <el-form :model="form" :rules="rules" ref="formRef">
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="用户名"
            prefix-icon="User"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            prefix-icon="Lock"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            @click="handleLogin"
            style="width: 100%"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>

      <div class="register-link">
        没有账号？
        <el-link type="primary" @click="showRegister = true">去注册</el-link>
      </div>
    </el-card>

    <!-- 注册弹窗 -->
    <el-dialog v-model="showRegister" title="注册" width="400px">
      <el-form :model="registerForm" :rules="registerRules" ref="registerFormRef">
        <el-form-item prop="username" label="用户名">
          <el-input v-model="registerForm.username" />
        </el-form-item>
        <el-form-item prop="email" label="邮箱">
          <el-input v-model="registerForm.email" />
        </el-form-item>
        <el-form-item prop="password" label="密码">
          <el-input v-model="registerForm.password" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRegister = false">取消</el-button>
        <el-button type="primary" :loading="registerLoading" @click="handleRegister">注册</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { userApi } from '../api'

const router = useRouter()
const formRef = ref()
const registerFormRef = ref()

const loading = ref(false)
const registerLoading = ref(false)
const showRegister = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const registerForm = reactive({
  username: '',
  email: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const registerRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效邮箱', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  await formRef.value.validate()
  loading.value = true
  try {
    const res = await userApi.login(form)
    localStorage.setItem('token', res.access_token)
    ElMessage.success('登录成功')
    router.push('/')
  } finally {
    loading.value = false
  }
}

const handleRegister = async () => {
  await registerFormRef.value.validate()
  registerLoading.value = true
  try {
    await userApi.register(registerForm)
    ElMessage.success('注册成功，请登录')
    showRegister.value = false
    form.username = registerForm.username
  } finally {
    registerLoading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 400px;
}

.login-card h2 {
  margin: 0;
  text-align: center;
  color: #333;
}

.register-link {
  text-align: center;
  color: #666;
}
</style>
