<script setup>
import { ref, onMounted } from 'vue'

const staff = ref([])
const errorMessage = ref('')
const successMessage = ref('')
const showForm = ref(false)
const search = ref('')

const newStaff = ref({
    name: '',
    email: '',
    password: '',
    phone_number: '',
    designation: ''
})

async function getStaff() {
    try {
        const response = await fetch(
            'http://localhost:5000/api/admin/staff',
            { credentials: 'include' }
        )

        const data = await response.json()

        if (!response.ok) {
            errorMessage.value = data.error || data.message || 'Failed to load staff.'
            return
        }

        staff.value = data.staff_profiles
        errorMessage.value = ''
    } catch (error) {
        errorMessage.value = 'Failed to load staff list.'
    }
}

async function createStaff() {
    errorMessage.value = ''
    successMessage.value = ''

    try {
        const response = await fetch(
            'http://localhost:5000/api/admin/staff',
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify(newStaff.value)
            }
        )

        const data = await response.json()

        if (!response.ok) {
            errorMessage.value = data.error || data.message || 'Failed to create staff.'
            return
        }

        successMessage.value = data.message || 'Staff created successfully!'
        showForm.value = false

        newStaff.value = {
            name: '',
            email: '',
            password: '',
            phone_number: '',
            designation: ''
        }

        await getStaff()
    } catch (error) {
        errorMessage.value = 'Failed to create staff.'
    }
}

function filteredStaff() {
    const term = search.value.trim().toLowerCase()

    return staff.value.filter(member =>
        (member.name || '').toLowerCase().includes(term) ||
        (member.email || '').toLowerCase().includes(term) ||
        (member.employee_id || '').toLowerCase().includes(term) ||
        (member.designation || '').toLowerCase().includes(term)
    )
}

async function updateStatus(member, status) {
    errorMessage.value = ''
    successMessage.value = ''

    try {
        const response = await fetch(
            `http://localhost:5000/api/admin/staff/${member.id}/status`,
            {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ status })
            }
        )
        const data = await response.json()

        if (!response.ok) {
            throw new Error(data.error || data.message || 'Failed to update staff status.')
        }

        member.status = status
        successMessage.value = data.message || 'Staff status updated.'
    } catch (error) {
        errorMessage.value = error.message
    }
}

onMounted(getStaff)
</script>

<template>
    <div class="container mt-4 mb-5">

        <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
            <h2>Manage Staff</h2>
            <div class="d-flex gap-2 flex-wrap">
                <button
                    class="btn btn-primary"
                    @click="showForm = !showForm"
                >
                    {{ showForm ? 'Close Form' : 'Create Staff' }}
                </button>
                <router-link to="/admin" class="btn btn-outline-secondary">
                    Back to Dashboard
                </router-link>
            </div>
        </div>
        

        <form
            v-if="showForm"
            @submit.prevent="createStaff"
            class="card card-body mb-4"
        >
            <input
                v-model="newStaff.name"
                class="form-control mb-2"
                placeholder="Full Name"
                required
            >

            <input
                v-model="newStaff.email"
                type="email"
                class="form-control mb-2"
                placeholder="Email"
                required
            >

            <input
                v-model="newStaff.password"
                type="password"
                class="form-control mb-2"
                placeholder="Password"
                required
            >

            <input
                v-model="newStaff.phone_number"
                class="form-control mb-2"
                placeholder="Phone Number"
            >

            <input
                v-model="newStaff.designation"
                class="form-control mb-3"
                placeholder="Designation"
                required
            >

            <button type="submit" class="btn btn-success">
                Save Staff
            </button>
        </form>

        <p v-if="errorMessage" class="text-danger">
            {{ errorMessage }}
        </p>

        <p v-if="successMessage" class="text-success">
            {{ successMessage }}
        </p>

        <input
            v-model="search"
            class="form-control mb-3"
            placeholder="Search by name, email, employee ID or designation..."
        >

        <table class="table table-bordered mt-3">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Employee ID</th>
                    <th>Designation</th>
                    <th>Status</th>
                    <th>Actions</th>
                </tr>
            </thead>

            <tbody>
                <tr v-for="member in filteredStaff()" :key="member.id">
                    <td>{{ member.name }}</td>
                    <td>{{ member.email }}</td>
                    <td>{{ member.employee_id }}</td>
                    <td>{{ member.designation }}</td>
                    <td>{{ member.status }}</td>
                    <td>
                        <select
                            class="form-select"
                            :value="member.status"
                            @change="updateStatus(member, $event.target.value)"
                        >
                            <option value="active">Active</option>
                            <option value="inactive">Inactive</option>
                            <option value="blacklisted">Blacklisted</option>
                        </select>
                    </td>
                </tr>

                <tr v-if="filteredStaff().length === 0">
                    <td colspan="6" class="text-center">
                        No staff members found.
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
</template>