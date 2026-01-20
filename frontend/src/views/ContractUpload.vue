<template>
  <div class="contract-upload">
    <h2>Upload Contract</h2>
    <form @submit.prevent="handleUpload">
      <div>
        <label>Contract Number:</label>
        <input v-model="contractNumber" type="text" required />
      </div>
      <div>
        <label>Contract Type:</label>
        <select v-model="contractType" required>
          <option value="sales">Sales</option>
          <option value="purchase">Purchase</option>
          <option value="service">Service</option>
          <option value="employment">Employment</option>
        </select>
      </div>
      <div>
        <label>File:</label>
        <input @change="handleFileChange" type="file" required />
      </div>
      <button type="submit">Upload</button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const contractNumber = ref('')
const contractType = ref('sales')
const file = ref<File | null>(null)

const handleFileChange = (e: Event) => {
  const target = e.target as HTMLInputElement
  if (target.files) {
    file.value = target.files[0]
  }
}

const handleUpload = async () => {
  // TODO: Implement upload API call
  console.log('Uploading:', { contractNumber: contractNumber.value, contractType: contractType.value, file: file.value })
}
</script>

<style scoped>
.contract-upload {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}
</style>
