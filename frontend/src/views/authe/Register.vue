<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const name = ref('')
const email = ref('')
const password = ref('')
const phone_number = ref('')
const errorMessage = ref('')
const router = useRouter()

async function handleRegister() {
  errorMessage.value = ''

  try {
    const response = await fetch('http://localhost:5000/api/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        name: name.value,
        email: email.value,
        password: password.value,
        phone_number: phone_number.value
      })
    })

    const data = await response.json()

    if (!response.ok) {
      errorMessage.value =
        data.error || data.message || 'Unable to register.'
      return
    }

    await router.push('/login')
  } catch {
    errorMessage.value =
      'Unable to connect to the server. Please check that the backend is running.'
  }
}
</script>

<template>
  <div class="container min-vh-100 d-flex justify-content-center align-items-center">
    <div class="card shadow p-4" style="width: 400px;">

      <h2 class="text-center mb-4">
        Trekking Management Application
      </h2>

      <h4 class="text-center mb-4">Register</h4>

      <div v-if="errorMessage" class="alert alert-danger" role="alert">
        {{ errorMessage }}
      </div>

      <form @submit.prevent="handleRegister">

        <div class="mb-3">
          <label class="form-label">Name</label>
          <input
            type="text"
            class="form-control"
            placeholder="Enter your name"
            v-model="name"
          />
        </div>

        <div class="mb-3">
          <label class="form-label">Email</label>
          <input
            type="email"
            class="form-control"
            placeholder="Enter your email"
            v-model="email"
          />
        </div>

        <div class="mb-3">
          <label class="form-label">Phone Number</label>
          <input
            type="text"
            class="form-control"
            placeholder="Enter your phone number"
            v-model="phone_number"
          />
        </div>

        <div class="mb-3">
          <label class="form-label">Password</label>
          <input
            type="password"
            class="form-control"
            placeholder="Enter your password"
            v-model="password"
          />
        </div>

        <button type="submit" class="btn btn-primary w-100">
          Register
        </button>

      </form>

      <p class="text-center mt-3 mb-0">
        Already have an account?
        <a href="/login">Login here</a>
      </p>

    </div>
  </div>
</template>