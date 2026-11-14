
<script setup>
import { ref, onMounted } from 'vue'

const treks = ref([])
const loading = ref(true)
const errorMessage = ref('')
const savingTrekId = ref(null)
const successMessage = ref('')

const editingTrekId = ref(null)
const editSlots = ref(0)
const editStatus = ref('')

async function fetchTreks() {
  loading.value = true
  errorMessage.value = ''

  try {
    const response = await fetch(
      'http://localhost:5000/api/staff/treks',
      { credentials: 'include' }
    )

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.error || data.message || 'Failed to load treks.')
    }

    treks.value = data.treks || []
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

function startEditing(trek) {
  editingTrekId.value = trek.id
  editSlots.value = trek.available_slots
  editStatus.value = trek.status
  successMessage.value = ''
  errorMessage.value = ''
}

function cancelEditing() {
  editingTrekId.value = null
}

async function saveTrek(trek) {
  if (!Number.isInteger(Number(editSlots.value)) || Number(editSlots.value) < 0) {
    errorMessage.value = 'Available slots must be a whole number of 0 or more.'
    return
  }

  savingTrekId.value = trek.id
  errorMessage.value = ''
  successMessage.value = ''

  try {
    const response = await fetch(
      `http://localhost:5000/api/staff/treks/${trek.id}`,
      {
        method: 'PUT',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          available_slots: Number(editSlots.value),
          status: editStatus.value
        })
      }
    )

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.error || data.message || 'Failed to update trek.')
    }

    successMessage.value = `Trek "${trek.name}" updated successfully.`
    editingTrekId.value = null

    await fetchTreks()
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    savingTrekId.value = null
  }
}

onMounted(fetchTreks)
</script>

<template>
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <div>
        <h2>My Assigned Treks</h2>
        <p class="text-muted mb-0">
          View and manage your assigned treks.
        </p>
      </div>

      <router-link to="/staff" class="btn btn-outline-secondary">
        Dashboard
      </router-link>
    </div>

    <div v-if="successMessage" class="alert alert-success">
      {{ successMessage }}
    </div>

    <div v-if="errorMessage" class="alert alert-danger">
      {{ errorMessage }}
      <button
        class="btn btn-sm btn-outline-danger ms-2"
        @click="fetchTreks"
      >
        Retry
      </button>
    </div>

    <div v-if="loading" class="text-center py-4">
      Loading assigned treks...
    </div>

    <div v-else-if="treks.length === 0" class="alert alert-info">
      No treks have been assigned to you yet.
    </div>

    <div v-else class="row g-3">
      <div
        v-for="trek in treks"
        :key="trek.id"
        class="col-md-6 col-lg-4"
      >
        <div class="card shadow-sm h-100">
          <div class="card-body">
            <h5 class="card-title">{{ trek.name }}</h5>
            <p class="text-muted mb-2">{{ trek.location }}</p>
            <p>{{ trek.description || 'No description available.' }}</p>

            <ul class="list-unstyled small">
              <li><strong>Start:</strong> {{ trek.start_date }}</li>
              <li><strong>End:</strong> {{ trek.end_date }}</li>
              <li><strong>Duration:</strong> {{ trek.duration }} days</li>
              <li><strong>Difficulty:</strong> {{ trek.difficulty_level }}</li>
              <li><strong>Available Slots:</strong> {{ trek.available_slots }}</li>
            </ul>

            <span class="badge bg-primary">{{ trek.status }}</span>

            <div v-if="editingTrekId === trek.id" class="border rounded p-3 mt-3">
              <h6>Manage Trek</h6>

              <label class="form-label mt-2">Available Slots</label>
              <input
                v-model.number="editSlots"
                type="number"
                min="0"
                step="1"
                class="form-control"
              />

              <label class="form-label mt-3">Trek Status</label>
              <select v-model="editStatus" class="form-select">
                <option>Pending</option>
                <option>Approved</option>
                <option>Open</option>
                <option>Closed</option>
                <option>Completed</option>
              </select>

              <div class="d-flex gap-2 mt-3">
                <button
                  class="btn btn-success btn-sm"
                  :disabled="savingTrekId === trek.id"
                  @click="saveTrek(trek)"
                >
                  {{ savingTrekId === trek.id ? 'Saving...' : 'Save Changes' }}
                </button>

                <button
                  class="btn btn-outline-secondary btn-sm"
                  :disabled="savingTrekId === trek.id"
                  @click="cancelEditing"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>

          <div class="card-footer bg-white d-flex flex-wrap gap-2">
            <button
              class="btn btn-sm btn-primary"
              @click="startEditing(trek)"
            >
              Manage Trek
            </button>

            <router-link
              :to="`/staff/treks/${trek.id}/users`"
              class="btn btn-sm btn-outline-primary"
            >
              View Registered Users
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
