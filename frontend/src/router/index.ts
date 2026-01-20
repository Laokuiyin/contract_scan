import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import ContractUpload from '../views/ContractUpload.vue'
import ContractList from '../views/ContractList.vue'
import ContractDetail from '../views/ContractDetail.vue'
import ContractReview from '../views/ContractReview.vue'

const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    redirect: '/contracts'
  },
  {
    path: '/upload',
    name: 'Upload',
    component: ContractUpload
  },
  {
    path: '/contracts',
    name: 'ContractList',
    component: ContractList
  },
  {
    path: '/contracts/:id',
    name: 'ContractDetail',
    component: ContractDetail
  },
  {
    path: '/contracts/:id/review',
    name: 'ContractReview',
    component: ContractReview
  },
  {
    path: '/reviews',
    name: 'PendingReviews',
    component: ContractList
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
