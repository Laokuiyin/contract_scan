import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'multipart/form-data'
  }
})

// 上传合同
export const uploadContract = async (data: FormData) => {
  const response = await api.post('/contracts/upload', data)
  return response.data
}

// 获取合同列表
export const getContracts = async () => {
  const response = await api.get('/contracts/')
  return response.data
}

// 获取合同详情
export const getContractDetail = async (id: string) => {
  const response = await api.get(`/contracts/${id}`)
  return response.data
}

// 获取OCR识别文本
export const getContractOcrText = async (id: string) => {
  const response = await api.get(`/contracts/${id}/ocr-text`)
  return response.data
}

// 获取待审核合同
export const getPendingReviews = async () => {
  const response = await api.get('/contracts/pending-review')
  return response.data
}

// 提交审核
export const submitReview = async (data: any) => {
  const response = await api.post('/contracts/review', data)
  return response.data
}

// 删除单个合同
export const deleteContract = async (id: string) => {
  const response = await api.delete(`/contracts/${id}`)
  return response.data
}

// 批量删除合同
export const batchDeleteContracts = async (contractIds: string[]) => {
  const response = await api.post('/contracts/batch-delete', contractIds, {
    headers: {
      'Content-Type': 'application/json'
    }
  })
  return response.data
}

export default api
