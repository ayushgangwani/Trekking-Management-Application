<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const email = ref('')
const password = ref('')
const errorMessage = ref('')
const successMessage = ref('')
const router = useRouter()

async function handleLogin() {
    errorMessage.value = ''
    successMessage.value = ''

    try {
        const response = await fetch('http://localhost:5000/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({
                email: email.value,
                password: password.value
            })
        })

        const data = await response.json()

        if (!response.ok) {
            errorMessage.value = data.error || data.message || 'Unable to log in.'
            return
        }
       
        if (data.user?.role === 'admin') {
            await router.push('/admin')
        } else if (data.user?.role === 'staff') {
            await router.push('/staff')
        } else if (data.user?.role === 'user') {
            await router.push('/user')
        } else {
            errorMessage.value = 'Invalid user role.'
        }

        successMessage.value = 'Login successful.'
    } catch {
        errorMessage.value = 'Unable to connect to the server. Please check that the backend is running.'
    }
}
</script>


<template>
    <div class="container min-vh-100 d-flex justify-content-center align-items-center">
        <div class="card shadow p-4" style="width: 400px;">

            <h2 class="text-center mb-4">Trekking Management Application</h2>
            <h4 class="text-center mb-4">Login</h4>

            <div v-if="errorMessage" class="alert alert-danger" role="alert">
                {{ errorMessage }}
            </div>
            <div v-if="successMessage" class="alert alert-success" role="status">
                {{ successMessage }}
            </div>

            <form @submit.prevent="handleLogin">  
                <div class="mb-3">
                    <label class="form-label">Email:</label>
                    <input 
                    type="email" 
                    class="form-control" 
                    placeholder="Enter Your Email" 
                    v-model="email" >
                </div>

                <div class="mb-3">
                    <label class="form-label">Password:</label>
                    <input 
                    type="password" 
                    class="form-control" 
                    placeholder="Enter Your Password" 
                    v-model="password">
                </div>

                <button type="submit" class="btn btn-primary w-100">Login</button>
            </form>

            <p class="text-center mt-3 mb-0">Don't have an account? <a href="/register">Register here</a></p>
        </div>
    </div>
</template>
