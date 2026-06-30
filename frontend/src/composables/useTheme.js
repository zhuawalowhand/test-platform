import { ref, watch } from 'vue'

// 模块级单例，所有组件共享同一个 ref
const isDark = ref(localStorage.getItem('theme') === 'dark')

// 初始化 DOM class
if (isDark.value) {
  document.documentElement.classList.add('dark')
}

export function useTheme() {
  const toggleTheme = () => {
    isDark.value = !isDark.value
  }

  // 监听变化同步到 DOM 和 localStorage
  watch(isDark, (val) => {
    if (val) {
      document.documentElement.classList.add('dark')
      localStorage.setItem('theme', 'dark')
    } else {
      document.documentElement.classList.remove('dark')
      localStorage.setItem('theme', 'light')
    }
  }, { immediate: true })

  return { isDark, toggleTheme }
}
