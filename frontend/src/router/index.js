import { createRouter, createWebHistory } from 'vue-router'

import Login from '../views/authe/login.vue'
import Register from '../views/authe/Register.vue'

import AdminDashboard from '../views/admin/AdminDashboard.vue'
import AdminTreks from '../views/admin/AdminTreks.vue'
import AdminStaff from '../views/admin/AdminStaff.vue'
import AdminUsers from '../views/admin/AdminUsers.vue'
import AdminBookings from '../views/admin/AdminBookings.vue'

import StaffDashboard from '../views/staff/StaffDashboard.vue'
import StaffTreks from '../views/staff/StaffTreks.vue'
import StaffTrekUsers from '../views/staff/StaffTrekUsers.vue'
import StaffRegisteredUsers from '../views/staff/StaffRegisteredUsers.vue'

import UserDashboard from '../views/user/UserDashboard.vue'
import UserTreks from '../views/user/UserTreks.vue'
import UserBookings from '../views/user/UserBookings.vue'
import UserProfile from '../views/user/UserProfile.vue'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: Login
  },
  {
    path: '/register',
    name: 'register',
    component: Register
  },

  // Admin pages
  {
    path: '/admin',
    name: 'admin',
    component: AdminDashboard,
    meta: { requiresAuth: true, role: 'admin' }
  },
  {
    path: '/admin/treks',
    name: 'admin-treks',
    component: AdminTreks,
    meta: { requiresAuth: true, role: 'admin' }
  },
  {
    path: '/admin/staff',
    name: 'admin-staff',
    component: AdminStaff,
    meta: { requiresAuth: true, role: 'admin' }
  },
  {
    path: '/admin/users',
    name: 'admin-users',
    component: AdminUsers,
    meta: { requiresAuth: true, role: 'admin' }
  },
  {
    path: '/admin/bookings',
    name: 'admin-bookings',
    component: AdminBookings,
    meta: { requiresAuth: true, role: 'admin' }
  },

  // Staff pages
  {
    path: '/staff',
    name: 'staff',
    component: StaffDashboard,
    meta: { requiresAuth: true, role: 'staff' }
  },
  {
    path: '/staff/treks',
    name: 'staff-treks',
    component: StaffTreks,
    meta: { requiresAuth: true, role: 'staff' }
  },
  {
    path: '/staff/treks/:id/users',
    name: 'staff-trek-users',
    component: StaffTrekUsers,
    meta: { requiresAuth: true, role: 'staff' }
  },
  {
    path: '/staff/registered-users',
    name: 'staff-registered-users',
    component: StaffRegisteredUsers,
    meta: { requiresAuth: true, role: 'staff' }
  },

  // User pages
  {
    path: '/user',
    name: 'user-dashboard',
    component: UserDashboard,
    meta: { requiresAuth: true, role: 'user' }
  },
  {
    path: '/user/treks',
    name: 'user-treks',
    component: UserTreks,
    meta: { requiresAuth: true, role: 'user' }
  },
  {
    path: '/user/bookings',
    name: 'user-bookings',
    component: UserBookings,
    meta: { requiresAuth: true, role: 'user' }
  },
  {
    path: '/user/profile',
    name: 'user-profile',
    component: UserProfile,
    meta: { requiresAuth: true, role: 'user' }
  },

  // Unknown URLs go to login
  {
    path: '/:pathMatch(.*)*',
    redirect: '/login'
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// Check the Flask session before opening protected pages
router.beforeEach(async (to) => {
  if (!to.meta.requiresAuth) {
    return true
  }

  try {
    const response = await fetch(
      'http://localhost:5000/api/auth/check',
      {
        method: 'GET',
        credentials: 'include'
      }
    )

    if (!response.ok) {
      return {
        path: '/login',
        query: { redirect: to.fullPath }
      }
    }

    const data = await response.json()

    if (!data.authenticated) {
      return '/login'
    }

    if (data.role !== to.meta.role) {
      if (data.role === 'admin') return '/admin'
      if (data.role === 'staff') return '/staff'
      if (data.role === 'user') return '/user'

      return '/login'
    }

    return true
  } catch (error) {
    return '/login'
  }
})

export default router
