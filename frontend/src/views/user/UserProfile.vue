<script setup>
import { onMounted, ref } from 'vue'

const name = ref('')
const email = ref('')
const phoneNumber = ref('')
const password = ref('')
const loading = ref(true)
const saving = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

async function loadProfile() {
  loading.value = true
  errorMessage.value = ''

  try {
    const response = await fetch(
      'http://localhost:5000/api/user/profile',
      { credentials: 'include' }
    )
    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.error || data.message || 'Unable to load profile.')
    }

    name.value = data.name || ''
    email.value = data.email || ''
    phoneNumber.value = data.phone_number || ''
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

async function updateProfile() {
  saving.value = true
  errorMessage.value = ''
  successMessage.value = ''

  try {
    const response = await fetch(
      'http://localhost:5000/api/user/profile',
      {
        method: 'PUT',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: name.value.trim(),
          email: email.value.trim(),
          phone_number: phoneNumber.value.trim(),
          password: password.value
        })
      }
    )
    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.error || data.message || 'Unable to update profile.')
    }

    password.value = ''
    successMessage.value = data.message || 'Profile updated successfully.'
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    saving.value = false
  }
}

onMounted(loadProfile)
</script>

<template>
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2>My Profile</h2>
      <router-link to="/user" class="btn btn-outline-secondary">
        Dashboard
      </router-link>
    </div>

    <div v-if="loading" class="text-center py-4">Loading profile...</div>

    <form v-else class="card shadow-sm p-4" @submit.prevent="updateProfile">
      <div v-if="successMessage" class="alert alert-success">
        {{ successMessage }}
      </div>
      <div v-if="errorMessage" class="alert alert-danger">
        {{ errorMessage }}
      </div>

      <label class="form-label">Name</label>
      <input v-model="name" class="form-control mb-3" type="text" required />

      <label class="form-label">Email</label>
      <input v-model="email" class="form-control mb-3" type="email" required />

      <label class="form-label">Phone Number</label>
      <input v-model="phoneNumber" class="form-control mb-3" type="text" />

      <label class="form-label">New Password</label>
      <input
        v-model="password"
        class="form-control mb-3"
        type="password"
        minlength="6"
        placeholder="Leave blank to keep your current password"
      />

      <button class="btn btn-primary" type="submit" :disabled="saving">
        {{ saving ? 'Saving...' : 'Save Changes' }}
      </button>
    </form>
  </div>
</template>
