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
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: { title: '数据概览' }
      },
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
      },
      {
        path: 'environments',
        name: 'Environments',
        component: () => import('../views/Environments.vue'),
        meta: { title: '环境管理' }
      },
      {
        path: 'schedules',
        name: 'Schedules',
        component: () => import('../views/Schedules.vue'),
        meta: { title: '定时任务' }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('../views/Settings.vue'),
        meta: { title: '个人设置' }
      },
      {
        path: 'testcases/:id',
        name: 'TestCaseDetail',
        component: () => import('../views/TestCaseDetail.vue'),
        meta: { title: '用例详情' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from) => {
  const token = localStorage.getItem('token')
  if (to.path !== '/login' && !token) {
    return '/login'
  }
})

export default router
