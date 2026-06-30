<template>
  <el-container class="layout-container">
    <el-aside width="200px">
      <div class="logo">
        <h3>测试平台</h3>
      </div>
      <el-menu
        :default-active="route.path"
        router
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
      >
        <el-menu-item index="/dashboard">
          <el-icon><HomeFilled /></el-icon>
          <span>数据概览</span>
        </el-menu-item>
        <el-menu-item index="/testcases">
          <el-icon><Document /></el-icon>
          <span>用例管理</span>
        </el-menu-item>
        <el-menu-item index="/reports">
          <el-icon><DataAnalysis /></el-icon>
          <span>测试报告</span>
        </el-menu-item>
        <el-menu-item index="/environments">
          <el-icon><Setting /></el-icon>
          <span>环境管理</span>
        </el-menu-item>
        <el-menu-item index="/schedules">
          <el-icon><Timer /></el-icon>
          <span>定时任务</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><UserFilled /></el-icon>
          <span>个人设置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header>
        <div class="header-right">
          <el-button @click="toggleTheme" :icon="isDark ? 'Sunny' : 'Moon'" circle size="small">
            {{ isDark ? '☀️' : '🌙' }}
          </el-button>
          <span>{{ username }}</span>
          <el-button type="danger" text @click="handleLogout">退出</el-button>
        </div>
      </el-header>

      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { userApi } from '../api'

const route = useRoute()
const router = useRouter()
const username = ref('')
const isDark = ref(localStorage.getItem('theme') === 'dark')

// 初始化主题
onMounted(() => {
  if (isDark.value) {
    document.documentElement.classList.add('dark')
  }
})

const toggleTheme = () => {
  isDark.value = !isDark.value
  if (isDark.value) {
    document.documentElement.classList.add('dark')
    localStorage.setItem('theme', 'dark')
  } else {
    document.documentElement.classList.remove('dark')
    localStorage.setItem('theme', 'light')
  }
}

onMounted(async () => {
  try {
    const user = await userApi.getMe()
    username.value = user.username
  } catch {
    router.push('/login')
  }
})

const handleLogout = () => {
  localStorage.removeItem('token')
  router.push('/login')
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.el-aside {
  background-color: #304156;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.logo h3 {
  margin: 0;
}

.el-header {
  background-color: var(--header-bg, #fff);
  border-bottom: 1px solid var(--border-color, #eee);
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}
</style>
