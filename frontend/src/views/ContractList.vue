<template>
  <div class="list-page">
    <NavBar />
    <div class="list-container">
      <div class="list-header">
        <h2>{{ pageTitle }}</h2>
        <el-button type="primary" @click="goToUpload">
          <el-icon><Plus /></el-icon>
          上传新合同
        </el-button>
      </div>

      <el-table :data="contracts" v-loading="loading" stripe>
        <el-table-column prop="contract_number" label="合同编号" width="180" />
        <el-table-column prop="contract_type" label="合同类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getTypeTagType(row.contract_type)">
              {{ getTypeLabel(row.contract_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="party_a_name" label="甲方名称" width="200">
          <template #default="{ row }">
            {{ row.party_a_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="party_b_name" label="乙方名称" width="200">
          <template #default="{ row }">
            {{ row.party_b_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="total_amount" label="合同金额" width="150">
          <template #default="{ row }">
            {{ row.total_amount ? `¥${formatAmount(row.total_amount)}` : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="upload_time" label="上传时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.upload_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="150">
          <template #default="{ row }">
            <el-button size="small" @click="viewDetails(row.id)">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && contracts.length === 0" description="暂无合同数据" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Plus } from '@element-plus/icons-vue'
import NavBar from '@/components/NavBar.vue'
import { getContracts, getPendingReviews } from '@/api'

const router = useRouter()
const route = useRoute()
const loading = ref(true)
const contracts = ref<any[]>([])

// 根据路由判断页面类型
const pageTitle = computed(() => {
  return route.path === '/reviews' ? '待审核合同' : '合同列表'
})

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

const formatAmount = (amount: number | string) => {
  if (!amount) return '0.00'
  const num = typeof amount === 'string' ? parseFloat(amount) : amount
  return num.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

const getTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    sales: '销售合同',
    purchase: '采购合同',
    service: '服务合同',
    employment: '劳动合同'
  }
  return labels[type] || type
}

const getTypeTagType = (type: string) => {
  const types: Record<string, any> = {
    sales: 'success',
    purchase: 'warning',
    service: 'info',
    employment: 'primary'
  }
  return types[type] || ''
}

const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    pending_ocr: '待OCR识别',
    ocr_processing: 'OCR处理中',
    pending_ai: '待AI提取',
    ai_processing: 'AI提取中',
    pending_review: '待审核',
    completed: '已完成',
    pending: '待处理',
    processing: '处理中',
    failed: '失败'
  }
  return labels[status] || status
}

const getStatusTagType = (status: string) => {
  const types: Record<string, any> = {
    pending_ocr: 'info',
    ocr_processing: 'warning',
    pending_ai: 'info',
    ai_processing: 'warning',
    pending_review: 'primary',
    completed: 'success',
    pending: 'info',
    processing: 'warning',
    failed: 'danger'
  }
  return types[status] || ''
}

const goToUpload = () => {
  router.push('/upload')
}

const viewDetails = (id: string) => {
  router.push(`/contracts/${id}`)
}

onMounted(async () => {
  try {
    // 根据路由判断调用哪个 API
    let data
    if (route.path === '/reviews') {
      data = await getPendingReviews()
      // 待审核页面：只显示状态为 pending_review 的合同
      const allContracts = data.contracts || data || []
      contracts.value = allContracts.filter((c: any) => c.status === 'pending_review')
    } else {
      data = await getContracts()
      contracts.value = data.contracts || data || []
    }
  } catch (error) {
    console.error('Failed to fetch contracts:', error)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.list-page {
  min-height: 100vh;
  background-color: #f5f7fa;
}

.list-container {
  max-width: 1400px;
  margin: 30px auto;
  padding: 30px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.list-header h2 {
  margin: 0;
  color: #303133;
}
</style>
