<template>
  <div class="contract-list">
    <h2>Contract List</h2>
    <div v-if="loading">Loading...</div>
    <div v-else>
      <table>
        <thead>
          <tr>
            <th>Contract Number</th>
            <th>Type</th>
            <th>Status</th>
            <th>Upload Time</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="contract in contracts" :key="contract.id">
            <td>{{ contract.contract_number }}</td>
            <td>{{ contract.contract_type }}</td>
            <td>{{ contract.status }}</td>
            <td>{{ formatDate(contract.upload_time) }}</td>
            <td>
              <button @click="viewDetails(contract.id)">View</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface Contract {
  id: string
  contract_number: string
  contract_type: string
  status: string
  upload_time: string
}

const loading = ref(true)
const contracts = ref<Contract[]>([])

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString()
}

const viewDetails = (id: string) => {
  console.log('View details:', id)
  // TODO: Navigate to detail view
}

onMounted(async () => {
  // TODO: Fetch contracts from API
  loading.value = false
})
</script>

<style scoped>
.contract-list {
  padding: 20px;
}
table {
  width: 100%;
  border-collapse: collapse;
}
th, td {
  padding: 10px;
  text-align: left;
  border-bottom: 1px solid #ddd;
}
</style>
