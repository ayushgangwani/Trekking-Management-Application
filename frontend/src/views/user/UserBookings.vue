
<script setup>
import { ref, onMounted } from 'vue'

const bookings = ref([])
const loading = ref(true)
const errorMessage = ref('')
const successMessage = ref('')
const cancellingId = ref(null)

async function fetchBookings() {
  loading.value = true
  errorMessage.value = ''

  try {
    const response = await fetch(
      'http://localhost:5000/api/bookings',
      { credentials: 'include' }
    )

    const data = await response.json()

    if (!response.ok) {
      throw new Error(
        data.error || data.message || 'Failed to load bookings.'
      )
    }

    bookings.value = data.bookings || []
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

async function cancelBooking(booking) {
  const confirmed = window.confirm(
    `Are you sure you want to cancel "${booking.trek_name}"?`
  )

  if (!confirmed) return

  cancellingId.value = booking.booking_id
  errorMessage.value = ''
  successMessage.value = ''

  try {
    const response = await fetch(
      `http://localhost:5000/api/bookings/${booking.booking_id}/cancel`,
      {
        method: 'PUT',
        credentials: 'include'
      }
    )

    const data = await response.json()

    if (!response.ok) {
      throw new Error(
        data.error || data.message || 'Failed to cancel booking.'
      )
    }

    successMessage.value = data.message || 'Booking cancelled successfully.'

    await fetchBookings()
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    cancellingId.value = null
  }
}

onMounted(fetchBookings)
</script>

<template>
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <div>
        <h2>My Bookings 🏕️</h2>
        <p class="text-muted mb-0">
          View and manage your trek bookings.
        </p>
      </div>

      <div class="d-flex gap-2">
        <router-link
          to="/user/treks"
          class="btn btn-outline-primary"
        >
          Explore Treks
        </router-link>
        <router-link to="/user" class="btn btn-secondary">
          Dashboard
        </router-link>
      </div>
    </div>

    <div v-if="successMessage" class="alert alert-success">
      {{ successMessage }}
    </div>

    <div v-if="errorMessage" class="alert alert-danger">
      {{ errorMessage }}
      <button
        class="btn btn-sm btn-outline-danger ms-2"
        @click="fetchBookings"
      >
        Retry
      </button>
    </div>

    <div v-if="loading" class="text-center py-5">
      Loading your bookings...
    </div>

    <div
      v-else-if="bookings.length === 0"
      class="alert alert-info"
    >
      You have no bookings yet.
      <router-link to="/user/treks" class="alert-link">
        Explore available treks
      </router-link>
    </div>

    <div v-else class="table-responsive">
      <table class="table table-bordered table-hover align-middle">
        <thead class="table-light">
          <tr>
            <th>Trek Name</th>
            <th>Location</th>
            <th>Start Date</th>
            <th>End Date</th>
            <th>Booking Date</th>
            <th>Status</th>
            <th>Action</th>
          </tr>
        </thead>

        <tbody>
          <tr
            v-for="booking in bookings"
            :key="booking.booking_id"
          >
            <td>{{ booking.trek_name }}</td>
            <td>{{ booking.location }}</td>
            <td>{{ booking.start_date }}</td>
            <td>{{ booking.end_date }}</td>
            <td>{{ booking.booking_date }}</td>
            <td>
              <span
                class="badge"
                :class="{
                  'bg-success': booking.status === 'Booked',
                  'bg-danger': booking.status === 'Cancelled',
                  'bg-primary': booking.status === 'Completed',
                  'bg-warning text-dark':
                    !['Booked', 'Cancelled', 'Completed'].includes(booking.status)
                }"
              >
                {{ booking.status }}
              </span>
            </td>
            <td>
              <button
                v-if="!['Cancelled', 'Completed'].includes(booking.status)"
                class="btn btn-sm btn-danger"
                :disabled="cancellingId === booking.booking_id"
                @click="cancelBooking(booking)"
              >
                {{
                  cancellingId === booking.booking_id
                    ? 'Cancelling...'
                    : 'Cancel Booking'
                }}
              </button>

              <span v-else class="text-muted small">
                No action
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

  </div>
</template>
