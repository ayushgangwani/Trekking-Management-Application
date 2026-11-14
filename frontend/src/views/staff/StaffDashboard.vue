<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const staffName = ref('Staff')
const totalTreks = ref(0)
const assignedTreks = ref([])
const loading = ref(false)
const error = ref('')

async function loadDashboard() {
  loading.value = true
  error.value = ''

  try {
    const response = await fetch(
      'http://localhost:5000/api/staff/treks',
      {
        credentials: 'include'
      }
    )

    const data = await response.json()

    if (!response.ok) {
      throw new Error(
        data.error ||
        data.message ||
        'Could not load assigned treks.'
      )
    }

    assignedTreks.value = Array.isArray(data.treks) ? data.treks : []
    totalTreks.value = assignedTreks.value.length
  } catch (err) {
    error.value = err.message || 'Something went wrong.'
  } finally {
    loading.value = false
  }
}

async function logout() {
  try {
    const response = await fetch(
      'http://localhost:5000/api/logout',
      {
        method: 'POST',
        credentials: 'include'
      }
    )

    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
      throw new Error(
        data.message || data.error || 'Logout failed. Please try again.'
      )
    }

    await router.push('/login')
  } catch (err) {
    error.value = err.message
  }
}

onMounted(loadDashboard)
</script>

<template>
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
      <h2 class="mb-0">Staff Dashboard</h2>

      <button
        class="btn btn-outline-danger"
        @click="logout"
      >
        Logout
      </button>
    </div>

    <p class="text-muted mt-2">
      Welcome, {{ staffName }}!
    </p>

    <div v-if="error" class="alert alert-danger">
      {{ error }}

      <button
        class="btn btn-sm btn-outline-dark ms-2"
        @click="loadDashboard"
      >
        Retry
      </button>
    </div>

    <div class="row g-3 mt-2">
      <div class="col-md-4">
        <div class="card shadow-sm h-100">
          <div class="card-body">
            <h6 class="text-muted">My Assigned Treks</h6>
            <h2>{{ loading ? '...' : totalTreks }}</h2>
          </div>
        </div>
      </div>
    </div>

    <div class="card shadow-sm mt-4">
      <div class="card-body">
        <h5 class="card-title">Registered Users per Trek</h5>

        <div v-if="loading" class="text-muted">
          Loading participant counts...
        </div>
        <div v-else-if="assignedTreks.length === 0" class="text-muted">
          No treks have been assigned to you yet.
        </div>
        <div v-else class="table-responsive">
          <table class="table table-bordered table-striped mb-0">
            <thead class="table-light">
              <tr>
                <th>Trek</th>
                <th>Registered Users</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="trek in assignedTreks" :key="trek.id">
                <td>{{ trek.name }}</td>
                <td>{{ trek.registered_user_count }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <h5 class="mt-4">Staff Menu</h5>

    <div class="d-flex flex-wrap gap-2 mt-3">
      <router-link to="/staff/treks" class="btn btn-primary">
        My Assigned Treks
      </router-link>

      <router-link
        to="/staff/registered-users"
        class="btn btn-outline-primary"
      >
        Registered Users
      </router-link>
    </div>
  </div>
</template>
