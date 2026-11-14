<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const bookings = ref([])
const search = ref('')
const statusFilter = ref('All')
const errorMessage = ref('')
const successMessage = ref('')
const loading = ref(false)

const exporting = ref(false)
const exportMessage = ref('')
let exportTimer = null

const filteredBookings = computed(() => {
    const term = search.value.toLowerCase()

    return bookings.value.filter(booking => {
        const matchesSearch =
            String(booking.booking_id).includes(term) ||
            (booking.user_name || '').toLowerCase().includes(term) ||
            (booking.user_email || '').toLowerCase().includes(term) ||
            (booking.trek_name || '').toLowerCase().includes(term)

        const matchesStatus =
            statusFilter.value === 'All' ||
            booking.status === statusFilter.value

        return matchesSearch && matchesStatus
    })
})

async function getBookings() {
    loading.value = true
    errorMessage.value = ''

    try {
        const response = await fetch(
            'http://localhost:5000/api/admin/bookings',
            { credentials: 'include' }
        )

        const data = await response.json()

        if (!response.ok) {
            errorMessage.value =
                data.error || data.message || 'Failed to load bookings.'
            return
        }

        bookings.value = data.bookings || []
    } catch (error) {
        errorMessage.value = 'Cannot connect to backend.'
    } finally {
        loading.value = false
    }
}

async function updateStatus(booking, newStatus) {
    const oldStatus = booking.status
    errorMessage.value = ''
    successMessage.value = ''

    if (newStatus === oldStatus) return

    try {
        const response = await fetch(
            `http://localhost:5000/api/admin/bookings/${booking.booking_id}/status`,
            {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ status: newStatus })
            }
        )

        const data = await response.json()

        if (!response.ok) {
            errorMessage.value =
                data.error || data.message || 'Failed to update booking.'
            return
        }

        booking.status = data.status
        successMessage.value = data.message || 'Booking status updated.'
    } catch (error) {
        errorMessage.value = 'Cannot connect to backend.'
    }
}

function stopExportPolling() {
    if (exportTimer) {
        clearTimeout(exportTimer)
        exportTimer = null
    }
}

async function downloadExport(taskId) {
    exportMessage.value = 'Export complete! Downloading CSV...'

    try {
        const response = await fetch(
            `http://localhost:5000/api/admin/bookings/export/${encodeURIComponent(taskId)}/download`,
            { credentials: 'include' }
        )

        if (!response.ok) {
            const data = await response.json().catch(() => ({}))
            throw new Error(data.error || data.message || 'CSV download failed.')
        }

        const blob = await response.blob()
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')

        link.href = url
        link.download = 'bookings.csv'
        document.body.appendChild(link)
        link.click()
        link.remove()
        URL.revokeObjectURL(url)

        exportMessage.value = 'CSV downloaded successfully!'
    } catch (error) {
        errorMessage.value = error.message || 'CSV download failed.'
        exportMessage.value = ''
    } finally {
        exporting.value = false
    }
}

async function checkExportStatus(taskId, attempts = 0) {
    if (attempts >= 60) {
        exporting.value = false
        exportMessage.value = ''
        errorMessage.value = 'Export is taking too long. Please try again.'
        return
    }

    try {
        const response = await fetch(
            `http://localhost:5000/api/admin/bookings/export/${encodeURIComponent(taskId)}`,
            { credentials: 'include' }
        )

        const data = await response.json()

        if (!response.ok) {
            throw new Error(data.error || data.message || 'Could not check export status.')
        }

        if (data.status === 'SUCCESS') {
            stopExportPolling()
            await downloadExport(taskId)
            return
        }

        if (['FAILURE', 'REVOKED'].includes(data.status)) {
            throw new Error(data.message || 'CSV export failed.')
        }

        exportMessage.value = `Generating CSV... Status: ${data.status}`

        exportTimer = setTimeout(() => {
            checkExportStatus(taskId, attempts + 1)
        }, 1500)
    } catch (error) {
        stopExportPolling()
        exporting.value = false
        exportMessage.value = ''
        errorMessage.value = error.message || 'Could not check export status.'
    }
}

async function exportCSV() {
    if (exporting.value) return

    stopExportPolling()
    errorMessage.value = ''
    successMessage.value = ''
    exportMessage.value = 'Starting CSV export...'
    exporting.value = true

    try {
        const response = await fetch(
            'http://localhost:5000/api/admin/bookings/export',
            {
                method: 'POST',
                credentials: 'include'
            }
        )

        const data = await response.json()

        if (!response.ok) {
            throw new Error(data.error || data.message || 'Could not start CSV export.')
        }

        if (!data.task_id) {
            throw new Error('Export task ID was not returned by the server.')
        }

        exportMessage.value = 'Export started. Please wait...'
        await checkExportStatus(data.task_id)
    } catch (error) {
        exporting.value = false
        exportMessage.value = ''
        errorMessage.value = error.message || 'CSV export failed.'
    }
}

onMounted(getBookings)

onUnmounted(() => {
    stopExportPolling()
})
</script>

<template>
    <div class="container mt-4">
        <div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
            <h2>Manage Bookings</h2>

            <div class="d-flex gap-2 flex-wrap">
                <button
                    class="btn btn-success"
                    @click="exportCSV"
                    :disabled="exporting"
                >
                    {{ exporting ? 'Exporting...' : 'Export CSV' }}
                </button>

                <router-link to="/admin" class="btn btn-outline-secondary">
                    Back to Dashboard
                </router-link>
            </div>
        </div>

        <div v-if="exportMessage" class="alert alert-info">
            {{ exportMessage }}
        </div>

        <div v-if="errorMessage" class="alert alert-danger">
            {{ errorMessage }}
        </div>

        <div v-if="successMessage" class="alert alert-success">
            {{ successMessage }}
        </div>

        <div class="row g-2 mb-3">
            <div class="col-md-8">
                <input
                    v-model="search"
                    type="text"
                    class="form-control"
                    placeholder="Search booking ID, user, email or trek..."
                >
            </div>

            <div class="col-md-4">
                <select v-model="statusFilter" class="form-select">
                    <option value="All">All Statuses</option>
                    <option value="Booked">Booked</option>
                    <option value="Cancelled">Cancelled</option>
                    <option value="Completed">Completed</option>
                </select>
            </div>
        </div>

        <p v-if="loading">Loading bookings...</p>

        <div class="table-responsive">
            <table class="table table-bordered table-striped align-middle">
                <thead class="table-dark">
                    <tr>
                        <th>Booking ID</th>
                        <th>User</th>
                        <th>Email</th>
                        <th>Trek</th>
                        <th>Booking Date</th>
                        <th>Payment</th>
                        <th>Status</th>
                        <th>Update Status</th>
                    </tr>
                </thead>

                <tbody>
                    <tr
                        v-for="booking in filteredBookings"
                        :key="booking.booking_id"
                    >
                        <td>{{ booking.booking_id }}</td>
                        <td>{{ booking.user_name }}</td>
                        <td>{{ booking.user_email }}</td>
                        <td>{{ booking.trek_name }}</td>
                        <td>{{ booking.booking_date }}</td>
                        <td>{{ booking.payment_status || 'N/A' }}</td>
                        <td>{{ booking.status }}</td>
                        <td>
                            <select
                                class="form-select"
                                :value="booking.status"
                                @change="updateStatus(booking, $event.target.value)"
                            >
                                <option value="Booked">Booked</option>
                                <option value="Cancelled">Cancelled</option>
                                <option value="Completed">Completed</option>
                            </select>
                        </td>
                    </tr>

                    <tr v-if="!loading && filteredBookings.length === 0">
                        <td colspan="8" class="text-center">
                            No bookings found.
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <button
            class="btn btn-primary"
            @click="getBookings"
            :disabled="loading"
        >
            Refresh Bookings
        </button>
    </div>
</template>
