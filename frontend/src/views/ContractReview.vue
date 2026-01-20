<template>
  <div class="contract-review">
    <h2>Contract Review</h2>
    <div v-if="loading">Loading...</div>
    <div v-else-if="contract">
      <div class="review-section">
        <h3>Extracted Information</h3>

        <div class="field-group">
          <label>Total Amount:</label>
          <div>
            <p>AI Extracted: {{ contract.total_amount || 'N/A' }}</p>
            <input v-model="reviewData.total_amount" placeholder="Confirm value" />
          </div>
        </div>

        <div class="field-group">
          <label>Subject Matter:</label>
          <div>
            <p>AI Extracted: {{ contract.subject_matter || 'N/A' }}</p>
            <textarea v-model="reviewData.subject_matter" placeholder="Confirm value"></textarea>
          </div>
        </div>

        <div class="field-group">
          <label>Sign Date:</label>
          <div>
            <p>AI Extracted: {{ contract.sign_date || 'N/A' }}</p>
            <input v-model="reviewData.sign_date" type="date" />
          </div>
        </div>

        <div class="field-group">
          <label>Notes:</label>
          <textarea v-model="reviewData.notes" placeholder="Add review notes"></textarea>
        </div>

        <div class="actions">
          <button @click="approve">Approve</button>
          <button @click="requestRevision">Request Revision</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const loading = ref(true)
const contract = ref<any>(null)

const reviewData = ref({
  total_amount: '',
  subject_matter: '',
  sign_date: '',
  notes: ''
})

onMounted(async () => {
  const contractId = route.params.id
  // TODO: Fetch contract details from API
  console.log('Loading contract:', contractId)
  loading.value = false
})

const approve = () => {
  // TODO: Submit approval
  console.log('Approving with data:', reviewData.value)
}

const requestRevision = () => {
  // TODO: Request revision
  console.log('Requesting revision')
}
</script>

<style scoped>
.contract-review {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}
.field-group {
  margin-bottom: 20px;
}
.field-group label {
  display: block;
  font-weight: bold;
  margin-bottom: 5px;
}
.field-group input,
.field-group textarea {
  width: 100%;
  padding: 8px;
  margin-top: 5px;
}
.actions {
  margin-top: 20px;
}
.actions button {
  margin-right: 10px;
}
</style>
