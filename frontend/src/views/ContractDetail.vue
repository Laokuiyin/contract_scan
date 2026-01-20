<template>
  <div class="detail-page">
    <NavBar />
    <div class="detail-container" v-loading="loading">
      <div v-if="contract">
        <div class="detail-header">
          <el-button @click="goBack" :icon="ArrowLeft">返回</el-button>
          <h2>合同详情</h2>
        </div>

        <el-card class="info-card">
          <template #header>
            <div class="card-header">
              <span>基本信息</span>
            </div>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="合同编号">{{ contract.contract_number }}</el-descriptions-item>
            <el-descriptions-item label="合同类型">
              <el-tag :type="getTypeTagType(contract.contract_type)">
                {{ getTypeLabel(contract.contract_type) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="getStatusTagType(contract.status)">
                {{ getStatusLabel(contract.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="上传时间">{{ formatDate(contract.upload_time) }}</el-descriptions-item>
            <el-descriptions-item label="创建者">{{ contract.created_by || '-' }}</el-descriptions-item>
            <el-descriptions-item label="文件路径">{{ contract.file_path }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card class="info-card" v-if="contract.total_amount || contract.subject_matter || contract.sign_date">
          <template #header>
            <div class="card-header">
              <span>提取信息</span>
            </div>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="合同金额">{{ contract.total_amount || '-' }}</el-descriptions-item>
            <el-descriptions-item label="合同标的">{{ contract.subject_matter || '-' }}</el-descriptions-item>
            <el-descriptions-item label="签署日期">{{ formatDate(contract.sign_date) }}</el-descriptions-item>
            <el-descriptions-item label="生效日期">{{ formatDate(contract.effective_date) }}</el-descriptions-item>
            <el-descriptions-item label="到期日期">{{ formatDate(contract.expire_date) }}</el-descriptions-item>
            <el-descriptions-item label="置信度">
              <el-progress
                v-if="contract.confidence_score"
                :percentage="Math.round(contract.confidence_score * 100)"
                :color="getConfidenceColor(contract.confidence_score)"
              />
              <span v-else>-</span>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card class="info-card" v-if="contract.requires_review">
          <template #header>
            <div class="card-header">
              <span>审核操作</span>
            </div>
          </template>
          <el-alert
            title="此合同需要人工审核"
            type="warning"
            description="AI 提取的信息需要人工确认和修正"
            show-icon
            :closable="false"
            style="margin-bottom: 20px"
          />
          <el-button type="primary" @click="goToReview">开始审核</el-button>
        </el-card>

        <el-card class="info-card">
          <template #header>
            <div class="card-header">
              <span>操作</span>
            </div>
          </template>
          <el-space>
            <el-button
              type="primary"
              :loading="ocrProcessing"
              @click="triggerOCR"
              :disabled="contract.status === 'ocr_processing' || contract.status === 'pending_ai'"
            >
              {{ ocrProcessing ? 'OCR处理中...' : '触发OCR识别' }}
            </el-button>
            <el-button @click="goBack">返回列表</el-button>
          </el-space>
          <div style="margin-top: 10px; color: #909399; font-size: 12px;">
            <el-icon><InfoFilled /></el-icon>
            <span style="margin-left: 5px">
              当前OCR提供方：{{ contract.ocr_text_path ? '已识别' : '未识别' }}
            </span>
          </div>
        </el-card>
      </div>

      <el-empty v-else-if="!loading" description="合同不存在" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ArrowLeft, InfoFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import NavBar from '@/components/NavBar.vue'
import { getContractDetail } from '@/api'
import axios from 'axios'

const router = useRouter()
const route = useRoute()
const loading = ref(true)
const ocrProcessing = ref(false)
const contract = ref<any>(null)

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
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
    completed: '已完成'
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
    completed: 'success'
  }
  return types[status] || ''
}

const getConfidenceColor = (score: number) => {
  if (score >= 0.8) return '#67c23a'
  if (score >= 0.6) return '#e6a23c'
  return '#f56c6c'
}

const goBack = () => {
  router.back()
}

const goToReview = () => {
  router.push(`/contracts/${route.params.id}/review`)
}

const triggerOCR = async () => {
  ocrProcessing.value = true
  try {
    const id = route.params.id as string
    const response = await axios.post(`/api/contracts/${id}/ocr`)
    contract.value = response.data
    ElMessage.success('OCR识别完成！')
  } catch (error: any) {
    console.error('OCR failed:', error)
    ElMessage.error(error.response?.data?.detail || 'OCR识别失败')
  } finally {
    ocrProcessing.value = false
  }
}

onMounted(async () => {
  try {
    const id = route.params.id as string
    contract.value = await getContractDetail(id)
  } catch (error: any) {
    console.error('Failed to fetch contract detail:', error)
    ElMessage.error(error.response?.data?.detail || '获取合同详情失败')
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.detail-page {
  min-height: 100vh;
  background-color: #f5f7fa;
}

.detail-container {
  max-width: 1200px;
  margin: 30px auto;
  padding: 30px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 30px;
}

.detail-header h2 {
  margin: 0;
  color: #303133;
}

.info-card {
  margin-bottom: 20px;
}

.card-header {
  font-weight: 600;
  color: #303133;
}
</style>
