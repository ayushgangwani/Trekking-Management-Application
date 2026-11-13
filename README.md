# Trekking Management Application (TMA)

TMA is a web application for managing trekking activities, staff, users, and
bookings. It provides separate workflows for administrators, trek staff, and
trekkers.

## Features

### Admin

- Create, update, and delete treks
- Manage trek staff and assign staff to treks
- Manage users and bookings
- Update user and staff status
- View trek and booking information

### Trek Staff

- View assigned treks
- View registered users for assigned treks
- Update trek status
- Manage available trek slots

### User / Trekker

- Register, log in, and log out
- View available treks
- Book or cancel a trek
- View booking history and profile information

## Technologies

- **Backend:** Python, Flask, Flask-SQLAlchemy, SQLite
- **Frontend:** Vue 3, Vite, Vue Router, Bootstrap
- **Background tasks:** Celery and Redis
- **Email:** Gmail SMTP through Flask-Mail

## Prerequisites

- Python 3.10 or later
- Node.js `22.18.0` or later (or Node.js `24.12.0` or later)
- Redis running on `localhost:6379`

## Project Structure

```text
Trekking-Management-Application/
├── backend/
│   ├── app.py
│   ├── models.py
│   ├── routes.py
│   └── celery_app.py
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── .gitignore
└── README.md
```

The SQLite database, Celery schedule files, generated exports, environment
files, dependencies, and build output are local files and are excluded by
`.gitignore`.

## Run the Application After Downloading

The following steps assume Windows PowerShell. Open separate terminals for the
backend, frontend, Redis, and (optionally) Celery.

### 1. Download the project

Clone the repository and enter its folder:

```powershell
git clone https://github.com/ayushgangwani/Trekking-Management-Application.git
cd Trekking-Management-Application
```

If you downloaded a ZIP file instead, extract it and open PowerShell in the
extracted `Trekking-Management-Application` folder.

### 2. Configure and start the backend

Create a Python virtual environment in the project root and activate it:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell prevents activation, run PowerShell as your user and execute
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.

Install the backend dependencies:

```powershell
python -m pip install Flask Flask-Cors Flask-Mail Flask-SQLAlchemy celery python-dotenv redis
```

Create `backend/.env` with the Gmail credentials used for email notifications:

```env
TMA_MAIL_USERNAME=your-email@gmail.com
TMA_MAIL_PASSWORD=your-gmail-app-password
```

Use a Gmail app password, not your normal Gmail password. Never commit or
share this file.

Start Redis before starting the API. Install Redis using a Windows-supported
option such as Docker, WSL, or Memurai, then start it so that it is available
at `localhost:6379`. You can verify the connection with:

```powershell
redis-cli ping
```

The expected response is `PONG`.

In the first terminal, start the Flask API:

```powershell
cd backend
python app.py
```

The API is available at `http://localhost:5000`.

### 3. Install and start the frontend

In a second terminal, from the project root:

```powershell
cd frontend
npm install
npm run dev
```

Open the frontend URL shown by Vite, normally
`http://localhost:5173`.

### 4. Start background tasks (optional)

The application uses Celery for booking reminders and monthly reports. Redis
must be running first. In a third terminal, activate the virtual environment
again and start a worker from the `backend` directory:

```powershell
cd path\to\Trekking-Management-Application
.\.venv\Scripts\Activate.ps1
cd backend
celery -A celery_app.celery worker --loglevel=info
```

To enable scheduled reminders and reports, start Celery Beat in another
terminal:

```powershell
cd path\to\Trekking-Management-Application
.\.venv\Scripts\Activate.ps1
cd backend
celery -A celery_app.celery beat --loglevel=info
```

## Manual Setup Reference

The commands below are the individual setup and development commands.

### Backend

Create and activate a virtual environment from the repository root:

```sh
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the backend dependencies:

```sh
pip install Flask Flask-Cors Flask-Mail Flask-SQLAlchemy celery python-dotenv redis
```

```sh
cd backend
python app.py
```

### Frontend

```sh
cd frontend
npm install
npm run dev
```

For a production build:

```sh
npm run build
```

### Celery

Redis must be running before starting Celery. From the `backend` directory,
start a worker:

```sh
celery -A celery_app.celery worker --loglevel=info
```

To run scheduled reminders and reports, start Celery Beat in another terminal:

```sh
celery -A celery_app.celery beat --loglevel=info
```
