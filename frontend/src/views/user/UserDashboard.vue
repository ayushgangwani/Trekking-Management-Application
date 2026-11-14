<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const userName = ref('Trekker')
const totalTreks = ref(0)
const totalBookings = ref(0)
const activeBookings = ref(0)
const loading = ref(true)
const errorMessage = ref('')

// CSV Export states
const exportLoading = ref(false)
const exportTaskId = ref('')
const exportStatus = ref('')
const exportMessage = ref('')
let pollingInterval = null

async function loadDashboard() {
  loading.value = true
  errorMessage.value = ''

  try {
    // Load logged-in user's profile
    const profileResponse = await fetch(
      'http://localhost:5000/api/user/profile',
      { credentials: 'include' }
    )

    const profileData = await profileResponse.json()

    if (!profileResponse.ok) {
      throw new Error(
        profileData.message ||
        profileData.error ||
        'Could not load your profile.'
      )
    }

    userName.value = profileData.name || 'Trekker'

    // Load available treks
    const trekResponse = await fetch(
      'http://localhost:5000/api/treks',
      { credentials: 'include' }
    )

    const trekData = await trekResponse.json()

    if (!trekResponse.ok) {
      throw new Error(
        trekData.error || trekData.message ||
        'Could not load treks.'
      )
    }

    const treks = Array.isArray(trekData)
      ? trekData
      : trekData.treks || []

    totalTreks.value = treks.filter(
      trek =>
        trek.status?.toLowerCase() === 'open' &&
        Number(trek.available_slots) > 0
    ).length

    // Load this user's bookings
    const bookingResponse = await fetch(
      'http://localhost:5000/api/bookings',
      { credentials: 'include' }
    )

    const bookingData = await bookingResponse.json()

    if (!bookingResponse.ok) {
      throw new Error(
        bookingData.error || bookingData.message ||
        'Could not load your bookings.'
      )
    }

    const bookings = bookingData.bookings || []

    totalBookings.value = bookings.length

    activeBookings.value = bookings.filter(
      booking =>
        !['Cancelled', 'Completed'].includes(booking.status)
    ).length

  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

// Start CSV export
async function exportMyBookings() {
  exportLoading.value = true
  exportMessage.value = ''
  exportStatus.value = 'PENDING'

  try {
    const response = await fetch(
      'http://localhost:5000/api/user/export-bookings',
      {
        method: 'POST',
        credentials: 'include'
      }
    )

    const data = await response.json()

    if (!response.ok) {
      throw new Error(
        data.error || data.message || 'Could not start CSV export.'
      )
    }

    exportTaskId.value = data.task_id
    exportMessage.value = 'Your CSV export has started.'

    // Start checking task status
    startStatusPolling()

  } catch (error) {
    exportMessage.value = error.message
    exportStatus.value = 'FAILED'
    exportLoading.value = false
  }
}

// Start polling
function startStatusPolling() {
  if (pollingInterval) {
    clearInterval(pollingInterval)
  }

  checkExportStatus()

  pollingInterval = setInterval(() => {
    checkExportStatus()
  }, 2000)
}

// Check Celery task status
async function checkExportStatus() {
  try {
    const response = await fetch(
      `http://localhost:5000/api/user/export-bookings/${exportTaskId.value}`,
      { credentials: 'include' }
    )

    const data = await response.json()

    if (!response.ok) {
      throw new Error(
        data.error || 'Could not check export status.'
      )
    }

    exportStatus.value = data.status

    if (data.status === 'SUCCESS') {
      exportMessage.value = 'Your CSV is ready! You can download it now.'
      exportLoading.value = false
      stopStatusPolling()
    }

    if (data.status === 'FAILURE') {
      exportMessage.value = data.message || 'CSV export failed.'
      exportLoading.value = false
      stopStatusPolling()
    }

  } catch (error) {
    exportMessage.value = error.message
    exportStatus.value = 'FAILED'
    exportLoading.value = false
    stopStatusPolling()
  }
}

// Stop polling
function stopStatusPolling() {
  if (pollingInterval) {
    clearInterval(pollingInterval)
    pollingInterval = null
  }
}

// Download CSV
async function downloadMyBookings() {
  try {
    const response = await fetch(
      `http://localhost:5000/api/user/export-bookings/${exportTaskId.value}/download`,
      { credentials: 'include' }
    )

    if (!response.ok) {
      const data = await response.json()
      throw new Error(data.error || 'CSV download failed.')
    }

    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)

    const link = document.createElement('a')
    link.href = url
    link.download = 'my_trekking_history.csv'

    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    window.URL.revokeObjectURL(url)

    exportMessage.value = 'CSV downloaded successfully!'

  } catch (error) {
    exportMessage.value = error.message
  }
}

// Logout
async function logout() {
  try {
    const response = await fetch(
      'http://localhost:5000/api/logout',
      {
        method: 'POST',
        credentials: 'include'
      }
    )

    if (!response.ok) {
      throw new Error('Logout failed. Please try again.')
    }

    await router.push('/login')

  } catch (error) {
    errorMessage.value = error.message
  }
}

onMounted(loadDashboard)

onUnmounted(() => {
  stopStatusPolling()
})
</script>

<template>
  <div class="container py-4">

    <!-- Header -->
    <div class="d-flex justify-content-between align-items-center mb-4">
      <div>
        <h2>Welcome, {{ userName }}! 🏔️</h2>
        <p class="text-muted mb-0">
          Ready for your next adventure?
        </p>
      </div>

      <div class="d-flex gap-2">
        <router-link to="/user/profile" class="btn btn-outline-primary">
          Profile
        </router-link>
        <button class="btn btn-outline-danger" @click="logout">
          Logout
        </button>
      </div>
    </div>

    <!-- Error message -->
    <div v-if="errorMessage" class="alert alert-warning">
      {{ errorMessage }}

      <button
        class="btn btn-sm btn-outline-dark ms-2"
        @click="loadDashboard"
      >
        Retry
      </button>
    </div>

    <!-- Statistics -->
    <div class="row g-3">

      <!-- Available treks -->
      <div class="col-md-6">
        <div class="card shadow-sm h-100">
          <div class="card-body">
            <h6 class="text-muted">Available Treks 🏕️</h6>

            <h2>{{ loading ? '...' : totalTreks }}</h2>

            <p class="mb-3">
              Treks currently open for booking
            </p>

            <router-link
              to="/user/treks"
              class="btn btn-primary"
            >
              Explore Treks
            </router-link>
          </div>
        </div>
      </div>

      <!-- Total bookings -->
      <div class="col-md-6">
        <div class="card shadow-sm h-100">
          <div class="card-body">
            <h6 class="text-muted">Total Bookings 📋</h6>

            <h2>{{ loading ? '...' : totalBookings }}</h2>

            <p class="mb-3">
              All your booking records
            </p>

            <router-link
              to="/user/bookings"
              class="btn btn-outline-primary"
            >
              View Bookings
            </router-link>
          </div>
        </div>
      </div>

    </div>

    <!-- CSV Export Section -->
    <div class="card shadow-sm mt-4">
      <div class="card-body">

        <h5 class="card-title">
          My Trekking History 📄
        </h5>

        <p class="text-muted">
          Export all your trekking booking records into a CSV file.
          You will also receive an email when the export is ready.
        </p>

        <button
          class="btn btn-success"
          :disabled="exportLoading"
          @click="exportMyBookings"
        >
          <span
            v-if="exportLoading"
            class="spinner-border spinner-border-sm me-2"
          ></span>

          {{ exportLoading
            ? 'Generating CSV...'
            : 'Export My Trekking History'
          }}
        </button>

        <!-- Export status -->
        <div
          v-if="exportMessage"
          class="alert mt-3 mb-0"
          :class="{
            'alert-success': exportStatus === 'SUCCESS',
            'alert-warning': exportLoading,
            'alert-danger': exportStatus === 'FAILED'
          }"
        >
          {{ exportMessage }}

          <div
            v-if="exportStatus === 'SUCCESS'"
            class="mt-2"
          >
            <button
              class="btn btn-primary btn-sm"
              @click="downloadMyBookings"
            >
              <i class="bi bi-download"></i>
              Download CSV
            </button>
          </div>
        </div>

      </div>
    </div>

    <!-- Refresh button -->
    <div class="text-end mt-4">
      <button
        class="btn btn-outline-secondary"
        :disabled="loading"
        @click="loadDashboard"
      >
        {{ loading ? 'Loading...' : 'Refresh Dashboard ↻' }}
      </button>
    </div>

  </div>
</template>
