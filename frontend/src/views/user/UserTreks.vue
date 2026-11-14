
<script setup>
import { ref, computed, onMounted } from 'vue'

const treks = ref([])
const loading = ref(true)
const errorMessage = ref('')
const searchQuery = ref('')
const selectedDifficulty = ref('All')
const selectedDuration = ref('All')

const bookingTrekId = ref(null)
const bookingMessage = ref('')
const bookingError = ref('')

async function fetchTreks() {
  loading.value = true
  errorMessage.value = ''

  try {
    const response = await fetch(
      'http://localhost:5000/api/treks',
      { credentials: 'include' }
    )

    const data = await response.json()

    if (!response.ok) {
      throw new Error(
        data.error || data.message || 'Failed to load treks.'
      )
    }

    const allTreks = Array.isArray(data)
      ? data
      : data.treks || []

    treks.value = allTreks.filter(
      trek =>
        trek.status?.toLowerCase() === 'open' &&
        Number(trek.available_slots) > 0
    )
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

const filteredTreks = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()

  return treks.value.filter(trek => {
    const matchesSearch =
      (trek.name || '').toLowerCase().includes(query) ||
      (trek.location || '').toLowerCase().includes(query)

    const matchesDifficulty =
      selectedDifficulty.value === 'All' ||
      trek.difficulty_level === selectedDifficulty.value

    const duration = Number(trek.duration)
    const matchesDuration =
      selectedDuration.value === 'All' ||
      (selectedDuration.value === 'short' && duration <= 3) ||
      (selectedDuration.value === 'medium' && duration >= 4 && duration <= 7) ||
      (selectedDuration.value === 'long' && duration >= 8)

    return matchesSearch && matchesDifficulty && matchesDuration
  })
})

async function bookTrek(trek) {
  bookingTrekId.value = trek.id
  bookingMessage.value = ''
  bookingError.value = ''

  try {
    const response = await fetch(
      'http://localhost:5000/api/bookings',
      {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          trek_id: trek.id
        })
      }
    )

    const data = await response.json()

    if (!response.ok) {
      throw new Error(
        data.error || data.message || 'Booking failed.'
      )
    }

    bookingMessage.value =
      `Successfully booked ${trek.name}!`

    await fetchTreks()
  } catch (error) {
    bookingError.value = error.message
  } finally {
    bookingTrekId.value = null
  }
}

onMounted(fetchTreks)
</script>

<template>
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <div>
        <h2>Explore Treks 🏔️</h2>
        <p class="text-muted mb-0">
          Find your next adventure!
        </p>
      </div>

      <router-link to="/user" class="btn btn-outline-secondary">
        Dashboard
      </router-link>
    </div>

    <!-- Booking success message -->
    <div v-if="bookingMessage" class="alert alert-success">
      {{ bookingMessage }}
      <router-link
        to="/user/bookings"
        class="alert-link ms-2"
      >
        View My Bookings
      </router-link>
    </div>

    <!-- Booking error message -->
    <div v-if="bookingError" class="alert alert-danger">
      {{ bookingError }}
    </div>

    <!-- Trek loading error -->
    <div v-if="errorMessage" class="alert alert-danger">
      {{ errorMessage }}
      <button
        class="btn btn-sm btn-outline-danger ms-2"
        @click="fetchTreks"
      >
        Retry
      </button>
    </div>

    <!-- Search and filters -->
    <div class="row g-3 mb-4">
      <div class="col-md-4">
        <input
          v-model="searchQuery"
          type="text"
          class="form-control"
          placeholder="Search by trek name or location..."
        />
      </div>

      <div class="col-md-4">
        <select v-model="selectedDifficulty" class="form-select">
          <option value="All">All Difficulty Levels</option>
          <option value="Easy">Easy</option>
          <option value="Moderate">Moderate</option>
          <option value="Hard">Hard</option>
        </select>
      </div>

      <div class="col-md-4">
        <select v-model="selectedDuration" class="form-select">
          <option value="All">All Durations</option>
          <option value="short">Up to 3 days</option>
          <option value="medium">4 to 7 days</option>
          <option value="long">8 or more days</option>
        </select>
      </div>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="text-center py-5">
      Loading available treks...
    </div>

    <!-- No treks available -->
    <div
      v-else-if="filteredTreks.length === 0"
      class="alert alert-info"
    >
      No available treks found. Try another search or check back later.
    </div>

    <!-- Trek cards -->
    <div v-else class="row g-3">
      <div
        v-for="trek in filteredTreks"
        :key="trek.id"
        class="col-md-6 col-lg-4"
      >
        <div class="card shadow-sm h-100">
          <div class="card-body">
            <h5 class="card-title">{{ trek.name }}</h5>

            <p class="text-muted mb-2">
              <i class="bi bi-geo-alt"></i>
              {{ trek.location }}
            </p>

            <p>
              {{ trek.description || 'No description available.' }}
            </p>

            <ul class="list-unstyled small">
              <li>
                <strong>Start Date:</strong> {{ trek.start_date }}
              </li>
              <li>
                <strong>End Date:</strong> {{ trek.end_date }}
              </li>
              <li>
                <strong>Duration:</strong> {{ trek.duration }} days
              </li>
              <li>
                <strong>Difficulty:</strong> {{ trek.difficulty_level }}
              </li>
              <li>
                <strong>Available Slots:</strong>
                {{ trek.available_slots }}
              </li>
            </ul>

            <span class="badge bg-success">
              {{ trek.status }}
            </span>
          </div>

          <div class="card-footer bg-white">
            <button
              class="btn btn-primary w-100"
              :disabled="bookingTrekId === trek.id"
              @click="bookTrek(trek)"
            >
              {{
                bookingTrekId === trek.id
                  ? 'Booking...'
                  : 'Book Trek'
              }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
