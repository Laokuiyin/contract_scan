<template>
  <div class="upload-page">
    <NavBar />
    <div class="upload-container">
      <h2>批量上传合同</h2>
      <el-form :model="form" label-width="120px" class="upload-form">
        <el-form-item label="合同编号前缀">
          <el-input v-model="form.contractNumber" placeholder="请输入合同编号前缀（可选）" />
          <div class="form-tip">如果输入前缀，每个文件会自动添加序号后缀，如：HT-001, HT-002</div>
        </el-form-item>

        <el-form-item label="合同类型">
          <el-select v-model="form.contractType" placeholder="请选择合同类型">
            <el-option label="销售合同" value="sales" />
            <el-option label="采购合同" value="purchase" />
            <el-option label="服务合同" value="service" />
            <el-option label="劳动合同" value="employment" />
          </el-select>
        </el-form-item>

        <el-form-item label="合同文件">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="100"
            :multiple="true"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            :file-list="fileList"
            accept=".pdf,.jpg,.jpeg,.png"
            drag
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              拖拽文件到此处或 <em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 PDF、JPG、PNG 格式，可多选，单次最多上传 100 个文件
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="uploading" :disabled="fileList.length === 0">
            {{ uploading ? `正在上传 (${uploadProgress.current}/${uploadProgress.total})` : `开始上传 (${fileList.length} 个文件)` }}
          </el-button>
          <el-button @click="handleReset" :disabled="uploading">清空</el-button>
        </el-form-item>
      </el-form>

      <!-- 上传进度 -->
      <div v-if="uploading || uploadResults.length > 0" class="upload-progress">
        <h3>上传结果</h3>
        <el-progress
          v-if="uploading"
          :percentage="uploadPercentage"
          :status="uploadStatus"
        >
          <span>{{ uploadProgress.current }} / {{ uploadProgress.total }}</span>
        </el-progress>

        <div class="result-list">
          <div
            v-for="(result, index) in uploadResults"
            :key="index"
            class="result-item"
            :class="result.status"
          >
            <el-icon v-if="result.status === 'success'"><success-filled /></el-icon>
            <el-icon v-else-if="result.status === 'uploading'"><loading /></el-icon>
            <el-icon v-else><circle-close-filled /></el-icon>
            <span class="file-name">{{ result.fileName }}</span>
            <span class="contract-number" v-if="result.contractNumber">({{ result.contractNumber }})</span>
            <span class="status-text">{{ result.message }}</span>
          </div>
        </div>

        <div v-if="!uploading && uploadResults.length > 0" class="upload-summary">
          <el-alert
            :title="`上传完成：成功 ${successCount} 个，失败 ${failCount} 个`"
            :type="failCount > 0 ? 'warning' : 'success'"
            show-icon
            :closable="false"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { UploadFilled, SuccessFilled, CircleCloseFilled, Loading } from '@element-plus/icons-vue'
import NavBar from '@/components/NavBar.vue'
import { uploadContract } from '@/api'

const router = useRouter()
const uploadRef = ref()
const uploading = ref(false)
const fileList = ref<any[]>([])
const uploadResults = ref<any[]>([])

const form = ref({
  contractNumber: '',
  contractType: 'sales'
})

const uploadProgress = ref({
  current: 0,
  total: 0
})

const uploadPercentage = computed(() => {
  if (uploadProgress.value.total === 0) return 0
  return Math.round((uploadProgress.value.current / uploadProgress.value.total) * 100)
})

const uploadStatus = computed(() => {
  if (uploadResults.value.some(r => r.status === 'error')) return 'exception'
  if (uploadPercentage.value === 100) return 'success'
  return undefined
})

const successCount = computed(() => uploadResults.value.filter(r => r.status === 'success').length)
const failCount = computed(() => uploadResults.value.filter(r => r.status === 'error').length)

const handleFileChange = (file: any, uploadFileList: any[]) => {
  fileList.value = uploadFileList
}

const handleFileRemove = (file: any, uploadFileList: any[]) => {
  fileList.value = uploadFileList
}

const generateContractNumber = (index: number) => {
  if (form.value.contractNumber) {
    // 使用前缀 + 序号（001, 002, ...）
    const num = String(index + 1).padStart(3, '0')
    return `${form.value.contractNumber}-${num}`
  }
  // 使用文件名
  return fileList.value[index]?.name?.split('.')[0] || `CONTRACT-${Date.now()}-${index}`
}

const handleSubmit = async () => {
  if (!form.value.contractType) {
    ElMessage.warning('请选择合同类型')
    return
  }
  if (fileList.value.length === 0) {
    ElMessage.warning('请选择合同文件')
    return
  }

  uploading.value = true
  uploadResults.value = []
  uploadProgress.value = {
    current: 0,
    total: fileList.value.length
  }

  // 按顺序上传每个文件
  for (let i = 0; i < fileList.value.length; i++) {
    const file = fileList.value[i]
    const contractNumber = generateContractNumber(i)

    // 添加到结果列表
    uploadResults.value.push({
      fileName: file.name,
      contractNumber: contractNumber,
      status: 'uploading',
      message: '上传中...'
    })

    try {
      const formData = new FormData()
      formData.append('contract_number', contractNumber)
      formData.append('contract_type', form.value.contractType)
      formData.append('file', file.raw)

      await uploadContract(formData)

      // 更新为成功
      uploadResults.value[i] = {
        fileName: file.name,
        contractNumber: contractNumber,
        status: 'success',
        message: '上传成功'
      }
    } catch (error: any) {
      console.error(`Upload failed for ${file.name}:`, error)
      // 更新为失败
      uploadResults.value[i] = {
        fileName: file.name,
        contractNumber: contractNumber,
        status: 'error',
        message: error.response?.data?.detail || '上传失败'
      }
    }

    uploadProgress.value.current = i + 1
  }

  uploading.value = false

  // 显示完成提示
  const successCount = uploadResults.value.filter(r => r.status === 'success').length
  const failCount = uploadResults.value.filter(r => r.status === 'error').length

  if (failCount === 0) {
    ElMessage.success(`全部上传成功！共 ${successCount} 个文件`)
  } else {
    ElMessage.warning(`上传完成：成功 ${successCount} 个，失败 ${failCount} 个`)
  }
}

const handleReset = () => {
  if (uploading.value) {
    ElMessage.warning('正在上传中，无法清空')
    return
  }
  form.value = {
    contractNumber: '',
    contractType: 'sales'
  }
  fileList.value = []
  uploadResults.value = []
  uploadRef.value?.clearFiles()
}
</script>

<style scoped>
.upload-page {
  min-height: 100vh;
  background-color: #f5f7fa;
}

.upload-container {
  max-width: 900px;
  margin: 30px auto;
  padding: 30px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.upload-container h2 {
  margin-top: 0;
  margin-bottom: 30px;
  color: #303133;
  font-size: 24px;
}

.upload-form {
  margin-top: 20px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

:deep(.el-upload-dragger) {
  width: 100%;
  min-height: 200px;
}

.upload-progress {
  margin-top: 30px;
  padding-top: 30px;
  border-top: 1px solid #ebeef5;
}

.upload-progress h3 {
  margin: 0 0 20px 0;
  color: #303133;
  font-size: 18px;
}

.result-list {
  margin-top: 20px;
  max-height: 400px;
  overflow-y: auto;
}

.result-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 8px;
  background-color: #f5f7fa;
}

.result-item.success {
  background-color: #f0f9ff;
  color: #67c23a;
}

.result-item.error {
  background-color: #fef0f0;
  color: #f56c6c;
}

.result-item.uploading {
  background-color: #ecf5ff;
  color: #409eff;
}

.result-item .el-icon {
  flex-shrink: 0;
}

.file-name {
  font-weight: 500;
  flex: 1;
}

.contract-number {
  color: #909399;
  font-size: 12px;
}

.status-text {
  font-size: 14px;
}

.upload-summary {
  margin-top: 20px;
}
</style>
