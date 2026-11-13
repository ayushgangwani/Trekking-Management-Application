
<script setup>
import { onMounted, ref } from 'vue'

const treks = ref([])
const search = ref('')
const isLoading = ref(true)
const errorMessage = ref('')
const successMessage = ref('')
const showForm = ref(false)

const staffList = ref([])
const selectedStaff = ref({})
const assigningTrekId = ref(null)

const newTrek = ref({
    name: '',
    location: '',
    description: '',
    duration: '',
    start_date: '',
    end_date: '',
    difficulty_level: 'Easy',
    available_slots: 10
})

async function getTreks() {
    isLoading.value = true
    errorMessage.value = ''

    try {
        const response = await fetch(
            'http://localhost:5000/api/admin/treks',
            { credentials: 'include' }
        )

        const data = await response.json()

        if (!response.ok) {
            errorMessage.value =
                data.message || data.error || 'Unable to load treks.'
            return
        }

        const trekList = Array.isArray(data) ? data : data.treks

        if (!Array.isArray(trekList)) {
            errorMessage.value = 'Invalid response received from server.'
            return
        }

        treks.value = trekList
    } catch {
        errorMessage.value =
            'Unable to connect to the server. Please check the backend.'
    } finally {
        isLoading.value = false
    }
}

async function getStaff() {
  try {
    const response = await fetch('http://localhost:5000/api/admin/staff', {
      credentials: 'include'
    })

    const data = await response.json()

    console.log('Staff API status:', response.status)
    console.log('Staff API response:', data)

    staffList.value = Array.isArray(data)
    ? data
    : data.staff_profiles || data.staff || data.staff_members || []
  } catch (error) {
    console.error('Error fetching staff:', error)
  }
}

async function createTrek() {
    errorMessage.value = ''
    successMessage.value = ''

    try {
        const response = await fetch(
            'http://localhost:5000/api/admin/treks',
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify(newTrek.value)
            }
        )

        const data = await response.json()

        if (!response.ok) {
            errorMessage.value = data.error || data.message || 'Unable to create trek.'
            return
        }

        successMessage.value = 'Trek created successfully!'
        showForm.value = false

        newTrek.value = {
            name: '',
            location: '',
            description: '',
            duration: '',
            start_date: '',
            end_date: '',
            difficulty_level: 'Easy',
            available_slots: 10
        }

        await getTreks()
    } catch {
        errorMessage.value = 'Unable to connect to the server.'
    }
}

async function deleteTrek(id) {
    if (!confirm('Are you sure you want to delete this trek?')) {
        return
    }

    errorMessage.value = ''
    successMessage.value = ''

    try {
        const response = await fetch(
            `http://localhost:5000/api/admin/treks/${id}`,
            {
                method: 'DELETE',
                credentials: 'include'
            }
        )

        const data = await response.json()

        if (!response.ok) {
            errorMessage.value = data.error || data.message || 'Unable to delete trek.'
            return
        }

        successMessage.value = 'Trek deleted successfully!'
        await getTreks()
    } catch {
        errorMessage.value = 'Unable to connect to the server.'
    }
}

const editTrek = ref(null)

function startEdit(trek) {
    errorMessage.value = ''
    successMessage.value = ''
    editTrek.value = { ...trek }
}

async function updateTrek() {
    errorMessage.value = ''
    successMessage.value = ''

    try {
        const response = await fetch(
            `http://localhost:5000/api/admin/treks/${editTrek.value.id}`,
            {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify(editTrek.value)
            }
        )

        const data = await response.json()

        if (!response.ok) {
            errorMessage.value = data.error || data.message || 'Unable to update trek.'
            return
        }

        successMessage.value = 'Trek updated successfully!'
        editTrek.value = null
        await getTreks()
    } catch {
        errorMessage.value = 'Unable to connect to the server.'
    }
}

async function assignStaff(trekId) {
    const staffId = selectedStaff.value[trekId]

    if (!staffId) {
        errorMessage.value = 'Please select a staff member first.'
        return
    }

    errorMessage.value = ''
    successMessage.value = ''
    assigningTrekId.value = trekId

    try {
        const response = await fetch(
            `http://localhost:5000/api/admin/treks/${trekId}/assign-staff`,
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({
                    staff_id: Number(staffId)
                })
            }
        )

        const data = await response.json()

        if (!response.ok) {
            errorMessage.value =
                data.error || data.message || 'Unable to assign staff.'
            return
        }

        successMessage.value = data.message || 'Staff assigned successfully!'
        selectedStaff.value[trekId] = ''
        await getTreks()
    } catch {
        errorMessage.value = 'Unable to connect to the server.'
    } finally {
        assigningTrekId.value = null
    }
}

const filteredTreks = () => {
    const term = search.value.trim().toLowerCase()

    return treks.value.filter(trek =>
        (trek.name || '').toLowerCase().includes(term) ||
        (trek.location || '').toLowerCase().includes(term) ||   
        (trek.difficulty_level || '').toLowerCase().includes(term)
    )
}

onMounted(() => {
    getTreks()
    getStaff()
})
</script>

<template>
    <div class="container mt-4 mb-5">

        <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
            <h2>Manage Treks</h2>
            <div class="d-flex gap-2 flex-wrap">
                <button
                    class="btn btn-primary"
                    @click="showForm = !showForm"
                >
                    {{ showForm ? 'Cancel' : '+ Add New Trek' }}
                </button>
                <router-link to="/admin" class="btn btn-outline-secondary">
                    Back to Dashboard
                </router-link>
            </div>
        </div>

         <input
            v-model="search"
            type="text"
            class="form-control mb-3"
            placeholder="Search by Trek Name, Location or Difficulty..."
        >

        <div v-if="successMessage" class="alert alert-success" role="status">
            {{ successMessage }}
        </div>

        <div v-if="errorMessage" class="alert alert-danger" role="alert">
            {{ errorMessage }}
        </div>

        <!-- Create Trek Form -->
        <div v-if="showForm" class="card shadow-sm p-4 mb-4">
            <h4 class="mb-3">Create New Trek</h4>

            <form @submit.prevent="createTrek">
                <div class="mb-3">
                    <label class="form-label">Trek Name</label>
                    <input v-model.trim="newTrek.name" type="text"
                        class="form-control" required />
                </div>

                <div class="mb-3">
                    <label class="form-label">Location</label>
                    <input v-model.trim="newTrek.location" type="text"
                        class="form-control" required />
                </div>

                <div class="mb-3">
                    <label class="form-label">Description</label>
                    <textarea v-model.trim="newTrek.description"
                        class="form-control" rows="3"></textarea>
                </div>

                <div class="mb-3">
                    <label class="form-label">Duration (days)</label>
                    <input v-model.number="newTrek.duration" type="number"
                        min="1" class="form-control" required />
                </div>

                <div class="row">
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Start Date</label>
                        <input v-model="newTrek.start_date" type="date"
                            class="form-control" required />
                    </div>

                    <div class="col-md-6 mb-3">
                        <label class="form-label">End Date</label>
                        <input v-model="newTrek.end_date" type="date"
                            class="form-control"
                            :min="newTrek.start_date || undefined" required />
                    </div>
                </div>

                <div class="mb-3">
                    <label class="form-label">Difficulty Level</label>
                    <select v-model="newTrek.difficulty_level"
                        class="form-select" required>
                        <option value="Easy">Easy</option>
                        <option value="Moderate">Moderate</option>
                        <option value="Hard">Hard</option>
                    </select>
                </div>

                <div class="mb-3">
                    <label class="form-label">Available Slots</label>
                    <input v-model.number="newTrek.available_slots"
                        type="number" min="0" class="form-control" required />
                </div>

                <button type="submit" class="btn btn-success">
                    Create Trek
                </button>

                <button type="button" class="btn btn-secondary ms-2"
                    @click="showForm = false">
                    Cancel
                </button>
            </form>
        </div>

        <!-- Edit Trek Form -->
        <div v-if="editTrek" class="card card-body mb-4">
            <h5>Edit Trek</h5>

            <form @submit.prevent="updateTrek">
                <input v-model="editTrek.name" class="form-control mb-2"
                    placeholder="Trek Name" required />

                <input v-model="editTrek.location" class="form-control mb-2"
                    placeholder="Location" required />

                <textarea v-model="editTrek.description"
                    class="form-control mb-2" placeholder="Description"></textarea>

                <label>Duration (days)</label>
                <input v-model.number="editTrek.duration" type="number"
                    min="1" class="form-control mb-2" required />

                <label>Start Date</label>
                <input v-model="editTrek.start_date" type="date"
                    class="form-control mb-2" required />

                <label>End Date</label>
                <input v-model="editTrek.end_date" type="date"
                    class="form-control mb-2" required />

                <label>Difficulty</label>
                <select v-model="editTrek.difficulty_level"
                    class="form-select mb-2">
                    <option>Easy</option>
                    <option>Moderate</option>
                    <option>Hard</option>
                </select>

                <label>Available Slots</label>
                <input v-model.number="editTrek.available_slots"
                    type="number" min="0" class="form-control mb-3" required />

                <label>Status</label>
                <select v-model="editTrek.status" class="form-select mb-3">
                    <option>Pending</option>
                    <option>Approved</option>
                    <option>Open</option>
                    <option>Closed</option>
                    <option>Completed</option>
                </select>

                <button type="submit" class="btn btn-success me-2">
                    Save Changes
                </button>

                <button type="button" class="btn btn-secondary"
                    @click="editTrek = null">
                    Cancel
                </button>
            </form>
        </div>

        <!-- Loading -->
        <div v-if="isLoading" class="alert alert-info">
            Loading treks...
        </div>

        <div v-else-if="treks.length === 0 && !errorMessage"
            class="alert alert-info">
            No treks have been added yet.
        </div>

        <!-- Trek List -->
        <div v-else-if="treks.length > 0" class="table-responsive">
            <table class="table table-bordered table-striped align-middle">
                <thead class="table-dark">
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Location</th>
                        <th>Difficulty</th>
                        <th>Duration</th>
                        <th>Available Slots</th>
                        <th>Status</th>
                        <th>Assigned Staff</th>
                        <th>Assign Staff</th>
                        <th>Actions</th>
                    </tr>
                </thead>

                <tbody>
                    <tr v-for="trek in filteredTreks()" :key="trek.id">
                        <td>{{ trek.id }}</td>
                        <td>{{ trek.name }}</td>
                        <td>{{ trek.location }}</td>
                        <td>{{ trek.difficulty_level }}</td>
                        <td>{{ trek.duration }}</td>
                        <td>{{ trek.available_slots }}</td>
                        <td>{{ trek.status }}</td>

                        <!-- Assigned Staff -->
                        <td>
                            <template v-if="trek.assigned_staff?.length">
                                <span
                                    v-for="staff in trek.assigned_staff"
                                    :key="staff.staff_id"
                                    class="d-block"
                                >
                                    {{ staff.name }}
                                    <span v-if="staff.employee_id" class="text-muted">
                                        ({{ staff.employee_id }})
                                    </span>
                                </span>
                            </template>
                            <span v-else class="text-muted">Not assigned</span>
                        </td>

                        <!-- Staff Assignment -->
                        <td style="min-width: 240px;">
                            <div v-if="staffList.length > 0"
                                class="d-flex gap-2">
                                <select v-model="selectedStaff[trek.id]"
                                    class="form-select form-select-sm">
                                    <option value="">Select Staff</option>

                                    <option
                                        v-for="staff in staffList"
                                        :key="staff.staff_id ?? staff.id"
                                        :value="staff.staff_id ?? staff.id"
                                    >
                                        {{ staff.name }}
                                        ({{ staff.employee_id || 'Staff' }})
                                    </option>
                                </select>

                                <button
                                    class="btn btn-primary btn-sm"
                                    :disabled="assigningTrekId === trek.id"
                                    @click="assignStaff(trek.id)"
                                >
                                    {{ assigningTrekId === trek.id
                                        ? 'Assigning...'
                                        : 'Assign' }}
                                </button>
                            </div>

                            <span v-else class="text-muted small">
                                No staff available
                            </span>
                        </td>

                        <!-- Existing Actions -->
                        <td style="min-width: 140px;">
                            <button
                                class="btn btn-warning btn-sm me-2 mb-1"
                                @click="startEdit(trek)"
                            >
                                Edit
                            </button>

                            <button
                                class="btn btn-danger btn-sm mb-1"
                                @click="deleteTrek(trek.id)"
                            >
                                Delete
                            </button>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

    </div>
</template>
