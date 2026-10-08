# Trekking Management Application (TMA)

## Project Overview

Trekking Management Application (TMA) is a web-based application designed to manage trekking activities in a simple and organized way.

The application provides different functionalities for Admin, Trek Staff, and Users.

## Features

### Admin
- Create, update and delete treks
- Manage trek staff
- Assign staff to treks
- Manage users
- Manage bookings
- Update user and staff status
- View trek and booking information

### Trek Staff
- View assigned treks
- View registered users for assigned treks
- Update trek status
- Manage available trek slots

### User / Trekker
- Register an account
- Login and logout
- View available treks
- Book a trek
- Cancel a booking
- View booking history
- View profile information

## Technologies Used

- Python
- Flask
- SQLAlchemy
- SQLite
- Vue.js
- Bootstrap
- Redis
- Celery
- Jinja2

## Project Structure

```text
TMA/
│
├── backend/
│   ├── app.py
│   ├── models.py
│   ├── routes.py
│   ├── celery_app.py
│   └── tma.db
│
├── frontend/
│   └── Vue.js application
│
├── README.md
└── .gitignore