import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue')
  },
  {
    path: '/',
    name: 'Layout',
    component: () => import('../views/Layout.vue'),
    redirect: '/testcases',
    children: [
      {
        path: 'testcases',
        name: 'TestCases',
        component: () => import('../views/TestCases.vue'),
        meta: { title: '用例管理' }
      },
      {
        path: 'reports',
        name: 'Reports',
        component: () => import('../views/Reports.vue'),
        meta: { title: '测试报告' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.path !== '/login' && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router
