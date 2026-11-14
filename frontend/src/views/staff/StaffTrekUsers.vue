
<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const trekId = route.params.id

const trekName = ref('')
const users = ref([])
const loading = ref(true)
const errorMessage = ref('')

async function fetchUsers() {
  loading.value = true
  errorMessage.value = ''

  try {
    const response = await fetch(
      `http://localhost:5000/api/staff/treks/${trekId}/users`,
      { credentials: 'include' }
    )

    const data = await response.json()

    if (!response.ok) {
      throw new Error(
        data.error || data.message || 'Failed to load registered users.'
      )
    }

    trekName.value = data.trek_name || 'Assigned Trek'
    users.value = data.users || []
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

onMounted(fetchUsers)
</script>

<template>
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <div>
        <h2>Registered Users</h2>
        <p class="text-muted mb-0">
          Trek: {{ trekName || `Trek #${trekId}` }}
        </p>
      </div>

      <router-link to="/staff/treks" class="btn btn-outline-secondary">
        Back to My Treks
      </router-link>
    </div>

    <div v-if="loading" class="text-center py-4">
      Loading registered users...
    </div>

    <div v-else-if="errorMessage" class="alert alert-danger">
      {{ errorMessage }}
      <button
        class="btn btn-sm btn-outline-danger ms-2"
        @click="fetchUsers"
      >
        Retry
      </button>
    </div>

    <template v-else>
      <div class="card shadow-sm">
        <div class="card-body">
          <h5>Total Registered Users: {{ users.length }}</h5>

          <div v-if="users.length === 0" class="alert alert-info mt-3 mb-0">
            No registered users found for this trek.
          </div>

          <div v-else class="table-responsive mt-3">
            <table class="table table-striped table-hover align-middle">
              <thead class="table-dark">
                <tr>
                  <th>User ID</th>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Phone</th>
                  <th>Booking Status</th>
                </tr>
              </thead>

              <tbody>
                <tr v-for="user in users" :key="user.booking_id">
                  <td>{{ user.user_id }}</td>
                  <td>{{ user.name }}</td>
                  <td>{{ user.email }}</td>
                  <td>{{ user.phone_number || 'Not provided' }}</td>
                  <td>
                    <span
                      class="badge"
                      :class="{
                        'bg-success': user.booking_status === 'Booked',
                        'bg-danger': user.booking_status === 'Cancelled',
                        'bg-primary': user.booking_status === 'Completed',
                        'bg-secondary': !['Booked', 'Cancelled', 'Completed'].includes(user.booking_status)
                      }"
                    >
                      {{ user.booking_status }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
