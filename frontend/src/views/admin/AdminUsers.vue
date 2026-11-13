<script setup>
import { ref, onMounted } from 'vue'

const users = ref([])
const search = ref('')
const errorMessage = ref('')
const successMessage = ref('')
const loading = ref(false)

async function getUsers() {
    loading.value = true
    errorMessage.value = ''

    try {
        const response = await fetch('http://localhost:5000/api/admin/users', {
            credentials: 'include'
        })

        const data = await response.json()

        if (!response.ok) {
            errorMessage.value = data.error || data.message || 'Failed to load users.'
            return
        }

        users.value = Array.isArray(data) ? data : (data.users || [])
    } catch (error) {
        errorMessage.value = 'Cannot connect to backend.'
    } finally {
        loading.value = false
    }
}

async function updateStatus(user, status) {
    errorMessage.value = ''
    successMessage.value = ''

    try {
        const response = await fetch(
            `http://localhost:5000/api/admin/users/${user.id}/status`,
            {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ status })
            }
        )

        const data = await response.json()

        if (!response.ok) {
            errorMessage.value = data.error || data.message || 'Failed to update status.'
            return
        }

        user.status = status
        successMessage.value = data.message || 'User status updated.'
    } catch (error) {
        errorMessage.value = 'Cannot connect to backend.'
    }
}

const filteredUsers = () => {
    const term = search.value.toLowerCase()

    return users.value.filter(user =>
        (user.name || '').toLowerCase().includes(term) ||
        (user.email || '').toLowerCase().includes(term) ||
        (user.role || '').toLowerCase().includes(term)
    )
}

onMounted(getUsers)
</script>

<template>
    <div class="container mt-4">
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h2>Manage Users</h2>
            <router-link to="/admin" class="btn btn-outline-secondary">
                Back to Dashboard
            </router-link>
        </div>

        <input
            v-model="search"
            type="text"
            class="form-control mb-3"
            placeholder="Search by name, email or role..."
        >

        <p v-if="errorMessage" class="text-danger">{{ errorMessage }}</p>
        <p v-if="successMessage" class="text-success">{{ successMessage }}</p>
        <p v-if="loading">Loading users...</p>

        <div class="table-responsive">
            <table class="table table-bordered table-striped">
                <thead class="table-dark">
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Role</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>

                <tbody>
                    <tr v-for="user in filteredUsers()" :key="user.id">
                        <td>{{ user.id }}</td>
                        <td>{{ user.name }}</td>
                        <td>{{ user.email }}</td>
                        <td>{{ user.role }}</td>
                        <td>{{ user.status }}</td>
                        <td>
                            <select
                                class="form-select"
                                :value="user.status"
                                @change="updateStatus(user, $event.target.value)"
                            >
                                <option value="active">Active</option>
                                <option value="inactive">Inactive</option>
                                <option value="blacklisted">Blacklisted</option>
                            </select>
                        </td>
                    </tr>

                    <tr v-if="!loading && filteredUsers().length === 0">
                        <td colspan="6" class="text-center">No users found.</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <button class="btn btn-primary" @click="getUsers">
            Refresh Users
        </button>
    </div>
</template>
