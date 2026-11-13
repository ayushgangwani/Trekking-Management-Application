<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const statistics = ref({
  total_users: 0,
  total_staff: 0,
  total_treks: 0,
  total_bookings: 0
})

const loading = ref(true)
const error = ref('')

// Monthly Report
const reportLoading = ref(false)
const reportError = ref('')
const reportMessage = ref('')
const monthlyReport = ref(null)
let reportTimer = null

// Booking Reminders
const reminderLoading = ref(false)
const reminderError = ref('')
const reminderMessage = ref('')
const reminderResult = ref(null)
let reminderTimer = null

async function fetchStatistics() {
  error.value = ''

  try {
    const response = await fetch(
      'http://localhost:5000/api/admin/statistics',
      { credentials: 'include' }
    )

    const data = await response.json()

    if (!response.ok) {
      throw new Error(
        data.message || data.error || 'Could not load dashboard statistics.'
      )
    }

    statistics.value = data
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

// Monthly Report functions
function stopReportPolling() {
  if (reportTimer) {
    clearTimeout(reportTimer)
    reportTimer = null
  }
}

async function checkReportStatus(taskId, attempts = 0) {
  if (attempts >= 60) {
    stopReportPolling()
    reportLoading.value = false
    reportMessage.value = ''
    reportError.value = 'Report is taking too long. Please try again.'
    return
  }

  try {
    const response = await fetch(
      `http://localhost:5000/api/admin/monthly-report/${encodeURIComponent(taskId)}`,
      { credentials: 'include' }
    )

    const data = await response.json()

    if (!response.ok) {
      throw new Error(
        data.message || data.error || 'Could not check report status.'
      )
    }

    if (data.status === 'SUCCESS') {
      stopReportPolling()

      if (!data.report) {
        throw new Error('Report data was not returned by the server.')
      }

      monthlyReport.value = data.report
      reportMessage.value = 'Monthly report generated successfully!'
      reportLoading.value = false
      return
    }

    if (['FAILURE', 'REVOKED'].includes(data.status)) {
      throw new Error(data.message || 'Report generation failed.')
    }

    reportMessage.value = `Generating report... Status: ${data.status}`

    reportTimer = setTimeout(
      () => checkReportStatus(taskId, attempts + 1),
      1500
    )
  } catch (err) {
    stopReportPolling()
    reportLoading.value = false
    reportMessage.value = ''
    reportError.value = err.message
  }
}

async function generateMonthlyReport() {
  if (reportLoading.value) return

  stopReportPolling()
  reportLoading.value = true
  reportError.value = ''
  reportMessage.value = 'Starting monthly report...'
  monthlyReport.value = null

  try {
    const response = await fetch(
      'http://localhost:5000/api/admin/monthly-report',
      {
        method: 'POST',
        credentials: 'include'
      }
    )

    const data = await response.json()

    if (!response.ok) {
      throw new Error(
        data.message || data.error || 'Could not start monthly report.'
      )
    }

    if (!data.task_id) {
      throw new Error('Report task ID was not returned by the server.')
    }

    reportMessage.value = 'Report started. Please wait...'
    await checkReportStatus(data.task_id)
  } catch (err) {
    stopReportPolling()
    reportLoading.value = false
    reportMessage.value = ''
    reportError.value = err.message
  }
}

// Booking Reminder functions
function stopReminderPolling() {
  if (reminderTimer) {
    clearTimeout(reminderTimer)
    reminderTimer = null
  }
}

async function checkReminderStatus(taskId, attempts = 0) {
  if (attempts >= 60) {
    stopReminderPolling()
    reminderLoading.value = false
    reminderMessage.value = ''
    reminderError.value = 'Reminders are taking too long. Please try again.'
    return
  }

  try {
    const response = await fetch(
      `http://localhost:5000/api/admin/booking-reminders/${encodeURIComponent(taskId)}`,
      { credentials: 'include' }
    )

    const data = await response.json()

    if (!response.ok) {
      throw new Error(
        data.message || data.error || 'Could not check reminder status.'
      )
    }

    if (data.status === 'SUCCESS') {
      stopReminderPolling()

      if (!data.report) {
        throw new Error('Reminder results were not returned by the server.')
      }

      reminderResult.value = data.report
      reminderMessage.value = 'Booking reminder task completed successfully!'
      reminderLoading.value = false
      return
    }

    if (['FAILURE', 'REVOKED'].includes(data.status)) {
      throw new Error(data.message || 'Booking reminder task failed.')
    }

    reminderMessage.value = `Processing reminders... Status: ${data.status}`

    reminderTimer = setTimeout(
      () => checkReminderStatus(taskId, attempts + 1),
      1500
    )
  } catch (err) {
    stopReminderPolling()
    reminderLoading.value = false
    reminderMessage.value = ''
    reminderError.value = err.message
  }
}

async function generateBookingReminders() {
  if (reminderLoading.value) return

  stopReminderPolling()
  reminderLoading.value = true
  reminderError.value = ''
  reminderMessage.value = 'Starting booking reminders...'
  reminderResult.value = null

  try {
    const response = await fetch(
      'http://localhost:5000/api/admin/booking-reminders',
      {
        method: 'POST',
        credentials: 'include'
      }
    )

    const data = await response.json()

    if (!response.ok) {
      throw new Error(
        data.message || data.error || 'Could not start booking reminders.'
      )
    }

    if (!data.task_id) {
      throw new Error('Reminder task ID was not returned by the server.')
    }

    reminderMessage.value = 'Reminder task started. Please wait...'
    await checkReminderStatus(data.task_id)
  } catch (err) {
    stopReminderPolling()
    reminderLoading.value = false
    reminderMessage.value = ''
    reminderError.value = err.message
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

    stopReportPolling()
    stopReminderPolling()
    await router.push('/login')
  } catch (err) {
    error.value = err.message
  }
}

onMounted(fetchStatistics)

onUnmounted(() => {
  stopReportPolling()
  stopReminderPolling()
})
</script>

<template>
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-4">
      <h2 class="mb-0">Admin Dashboard</h2>

      <button class="btn btn-outline-danger" @click="logout">
        Logout
      </button>
    </div>

    <!-- Dashboard Statistics -->
    <p v-if="loading">Loading statistics...</p>

    <div v-else-if="error" class="alert alert-danger">
      {{ error }}
      <button
        class="btn btn-sm btn-outline-dark ms-2"
        @click="fetchStatistics"
      >
        Retry
      </button>
    </div>

    <div v-else class="row g-3 mb-4">
      <div class="col-md-3 col-sm-6">
        <div class="card shadow-sm h-100">
          <div class="card-body">
            <h6 class="text-muted">Total Users</h6>
            <h2>{{ statistics.total_users }}</h2>
          </div>
        </div>
      </div>

      <div class="col-md-3 col-sm-6">
        <div class="card shadow-sm h-100">
          <div class="card-body">
            <h6 class="text-muted">Total Staff</h6>
            <h2>{{ statistics.total_staff }}</h2>
          </div>
        </div>
      </div>

      <div class="col-md-3 col-sm-6">
        <div class="card shadow-sm h-100">
          <div class="card-body">
            <h6 class="text-muted">Total Treks</h6>
            <h2>{{ statistics.total_treks }}</h2>
          </div>
        </div>
      </div>

      <div class="col-md-3 col-sm-6">
        <div class="card shadow-sm h-100">
          <div class="card-body">
            <h6 class="text-muted">Total Bookings</h6>
            <h2>{{ statistics.total_bookings }}</h2>
          </div>
        </div>
      </div>
    </div>

    <!-- Admin Menu -->
    <h5 class="mb-3">Admin Menu</h5>

    <div class="d-flex flex-wrap gap-2">
      <router-link to="/admin/treks" class="btn btn-primary">
        Manage Treks
      </router-link>

      <router-link to="/admin/staff" class="btn btn-primary">
        Manage Staff
      </router-link>

      <router-link to="/admin/users" class="btn btn-primary">
        Manage Users
      </router-link>

      <router-link to="/admin/bookings" class="btn btn-primary">
        Manage Bookings
      </router-link>
    </div>

    <!-- Monthly Report -->
    <div class="card shadow-sm mb-4 mt-4">
      <div class="card-body">
        <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
          <div>
            <h4 class="mb-1">Monthly Report</h4>
            <p class="text-muted mb-0">
              Generate a report of this month's booking activity.
            </p>
          </div>

          <button
            class="btn btn-success"
            @click="generateMonthlyReport"
            :disabled="reportLoading"
          >
            {{ reportLoading ? 'Generating...' : 'Generate Monthly Report' }}
          </button>
        </div>

        <div v-if="reportMessage" class="alert alert-info mt-3 mb-0">
          {{ reportMessage }}
        </div>

        <div v-if="reportError" class="alert alert-danger mt-3 mb-0">
          {{ reportError }}
        </div>

        <div v-if="monthlyReport" class="mt-4">
          <h5>{{ monthlyReport.month }}</h5>

          <div class="row g-3 mt-1">
            <div class="col-md-3 col-sm-6">
              <div class="card border-primary h-100">
                <div class="card-body">
                  <h6 class="text-muted">Total Bookings</h6>
                  <h3>{{ monthlyReport.total_bookings }}</h3>
                </div>
              </div>
            </div>

            <div class="col-md-3 col-sm-6">
              <div class="card border-success h-100">
                <div class="card-body">
                  <h6 class="text-muted">Completed Bookings</h6>
                  <h3>{{ monthlyReport.completed_bookings }}</h3>
                </div>
              </div>
            </div>

            <div class="col-md-3 col-sm-6">
              <div class="card border-danger h-100">
                <div class="card-body">
                  <h6 class="text-muted">Cancelled Bookings</h6>
                  <h3>{{ monthlyReport.cancelled_bookings }}</h3>
                </div>
              </div>
            </div>

            <div class="col-md-3 col-sm-6">
              <div class="card border-info h-100">
                <div class="card-body">
                  <h6 class="text-muted">Total Treks</h6>
                  <h3>{{ monthlyReport.total_treks }}</h3>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Booking Reminders -->
    <div class="card shadow-sm mb-4 mt-4">
      <div class="card-body">
        <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
          <div>
            <h4 class="mb-1">Booking Reminders</h4>
            <p class="text-muted mb-0">
              Check bookings for treks starting within the next 3 days.
            </p>
          </div>

          <button
            class="btn btn-warning"
            @click="generateBookingReminders"
            :disabled="reminderLoading"
          >
            {{ reminderLoading ? 'Processing...' : 'Generate Booking Reminders' }}
          </button>
        </div>

        <div v-if="reminderMessage" class="alert alert-info mt-3 mb-0">
          {{ reminderMessage }}
        </div>

        <div v-if="reminderError" class="alert alert-danger mt-3 mb-0">
          {{ reminderError }}
          <button
            class="btn btn-sm btn-outline-dark ms-2"
            @click="generateBookingReminders"
            :disabled="reminderLoading"
          >
            Retry
          </button>
        </div>

        <div v-if="reminderResult" class="mt-4">
          <h5>Reminder Task Results</h5>

          <div class="row g-3 mt-1">
            <div class="col-md-6">
              <div class="card border-success h-100">
                <div class="card-body">
                  <h6 class="text-muted">Reminders Generated</h6>
                  <h3>
                    {{ reminderResult.reminders_generated ?? 0 }}
                  </h3>
                </div>
              </div>
            </div>

            <div class="col-md-6">
              <div class="card border-info h-100">
                <div class="card-body">
                  <h6 class="text-muted">Checked On</h6>
                  <h5>{{ reminderResult.checked_on || 'N/A' }}</h5>
                </div>
              </div>
            </div>
          </div>

          <p class="text-muted small mt-3 mb-0">
            Reminder details are currently printed in the Celery worker
            console. This task does not send emails.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
