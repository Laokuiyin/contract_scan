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

        <el-card class="info-card">
          <template #header>
            <div class="card-header">
              <span>OCR识别结果</span>
            </div>
          </template>
          <div v-if="ocrLoading" v-loading="true" style="min-height: 100px"></div>
          <div v-else-if="ocrText" class="ocr-content">
            <pre>{{ ocrText }}</pre>
          </div>
          <el-empty v-else description="暂无OCR识别结果" :image-size="80" />
        </el-card>

        <el-card class="info-card">
          <template #header>
            <div class="card-header">
              <span>原始文件</span>
            </div>
          </template>
          <div v-if="filesLoading" v-loading="true" style="min-height: 100px"></div>
          <div v-else-if="files && files.length > 0">
            <el-table :data="files" style="width: 100%">
              <el-table-column prop="file_order" label="页码" width="80">
                <template #default="scope">
                  第 {{ scope.row.file_order + 1 }} 页
                </template>
              </el-table-column>
              <el-table-column prop="filename" label="文件名" />
              <el-table-column label="操作" width="200">
                <template #default="scope">
                  <el-button
                    size="small"
                    type="primary"
                    @click="downloadFile(scope.row.id, scope.row.filename)"
                    :icon="Download"
                  >
                    下载
                  </el-button>
                  <el-button
                    size="small"
                    type="danger"
                    @click="handleDeleteFile(scope.row)"
                    :icon="Delete"
                  >
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
          <el-empty v-else description="暂无文件" :image-size="80" />
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
import { ArrowLeft, InfoFilled, Download, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import NavBar from '@/components/NavBar.vue'
import { getContractDetail, getContractOcrText, getContractFiles, downloadContractFile, deleteContractFile } from '@/api'
import axios from 'axios'

const router = useRouter()
const route = useRoute()
const loading = ref(true)
const ocrProcessing = ref(false)
const contract = ref<any>(null)
const ocrText = ref<string>('')
const ocrLoading = ref(false)
const files = ref<any[]>([])
const filesLoading = ref(false)

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

    // 获取OCR识别文本
    await loadOcrText(id)

    // 获取文件列表
    await loadFiles(id)
  } catch (error: any) {
    console.error('Failed to fetch contract detail:', error)
    ElMessage.error(error.response?.data?.detail || '获取合同详情失败')
  } finally {
    loading.value = false
  }
})

const loadOcrText = async (id: string) => {
  ocrLoading.value = true
  try {
    const result = await getContractOcrText(id)
    if (result.ocr_text) {
      ocrText.value = result.ocr_text
    }
  } catch (error: any) {
    console.error('Failed to fetch OCR text:', error)
    // OCR文本加载失败不影响页面显示
  } finally {
    ocrLoading.value = false
  }
}

const loadFiles = async (id: string) => {
  filesLoading.value = true
  try {
    files.value = await getContractFiles(id)
  } catch (error: any) {
    console.error('Failed to fetch files:', error)
    ElMessage.error('加载文件列表失败')
  } finally {
    filesLoading.value = false
  }
}

const downloadFile = async (fileId: string, filename: string) => {
  try {
    const blob = await downloadContractFile(fileId)
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('下载成功')
  } catch (error: any) {
    console.error('Download failed:', error)
    ElMessage.error('下载失败')
  }
}

const handleDeleteFile = async (file: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除文件 "${file.filename}" 吗？删除后将清空该合同的甲方、乙方、合同金额等字段。`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const id = route.params.id as string
    await deleteContractFile(id, file.id)

    // 重新加载文件列表和合同详情
    await loadFiles(id)
    contract.value = await getContractDetail(id)

    ElMessage.success('删除成功')
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('Delete failed:', error)
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}
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

.ocr-content {
  max-height: 500px;
  overflow-y: auto;
  background-color: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  font-size: 14px;
  line-height: 1.8;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.ocr-content::-webkit-scrollbar {
  width: 6px;
}

.ocr-content::-webkit-scrollbar-thumb {
  background-color: #dcdfe6;
  border-radius: 3px;
}

.ocr-content::-webkit-scrollbar-thumb:hover {
  background-color: #c0c4cc;
}
</style>
