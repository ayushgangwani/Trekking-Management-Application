from flask import Flask, jsonify, request
from models import db, User, StaffProfile, Trek, TrekAssignment, Booking
from routes import (
    authentication_routes,
    admin_routes,
    staff_routes,
    user_routes
)
from werkzeug.security import generate_password_hash
from flask_cors import CORS
from flask_mail import Mail
from dotenv import load_dotenv
import redis
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)

# CORS Configuration
CORS(
    app,
    supports_credentials=True,
    resources={
        r"/api/*": {
            "origins": [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
            ]
        }
    },
)

# Redis Configuration
redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trekking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'trekking_management_secret_key'

# Gmail SMTP Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.getenv('TMA_MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('TMA_MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('TMA_MAIL_USERNAME')

# Initialize extensions
db.init_app(app)
mail = Mail(app)

def migrate_booking_history_schema():
    connection = db.engine.raw_connection()
    cursor = connection.cursor()

    try:
        def cancel_duplicate_active_bookings():
            cursor.execute("""
                UPDATE bookings
                SET status = 'Cancelled'
                WHERE status != 'Cancelled'
                  AND id NOT IN (
                      SELECT MAX(id)
                      FROM bookings
                      WHERE status != 'Cancelled'
                      GROUP BY user_id, trek_id
                  )
            """)

        indexes = cursor.execute("PRAGMA index_list('bookings')").fetchall()
        has_active_index = any(
            index[1] == "unique_active_user_trek_booking"
            for index in indexes
        )
        old_unique_index = None

        for index in indexes:
            if not index[2] or index[1] == "unique_active_user_trek_booking":
                continue
            columns = cursor.execute(
                f"PRAGMA index_info('{index[1]}')"
            ).fetchall()
            if [column[2] for column in columns] == ["user_id", "trek_id"]:
                old_unique_index = index[1]
                break

        if old_unique_index is None:
            if not has_active_index:
                cancel_duplicate_active_bookings()
                cursor.execute("""
                    CREATE UNIQUE INDEX unique_active_user_trek_booking
                    ON bookings (user_id, trek_id)
                    WHERE status != 'Cancelled'
                """)
                connection.commit()
            return

        cursor.execute("PRAGMA foreign_keys = OFF")
        cursor.execute("""
            CREATE TABLE bookings_new (
                id INTEGER NOT NULL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                trek_id INTEGER NOT NULL,
                booking_date DATETIME,
                status VARCHAR(20) NOT NULL,
                created_at DATETIME,
                reminder_sent BOOLEAN NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users (id),
                FOREIGN KEY(trek_id) REFERENCES treks (id)
            )
        """)
        cursor.execute("""
            INSERT INTO bookings_new (
                id, user_id, trek_id, booking_date, status,
                created_at, reminder_sent
            )
            SELECT
                id, user_id, trek_id, booking_date, status,
                created_at, reminder_sent
            FROM bookings
        """)
        cursor.execute("DROP TABLE bookings")
        cursor.execute("ALTER TABLE bookings_new RENAME TO bookings")
        cancel_duplicate_active_bookings()
        cursor.execute("""
            CREATE UNIQUE INDEX unique_active_user_trek_booking
            ON bookings (user_id, trek_id)
            WHERE status != 'Cancelled'
        """)
        cursor.execute("PRAGMA foreign_keys = ON")
        connection.commit()
    finally:
        connection.close()

# Register routes
authentication_routes(app)
admin_routes(app)
staff_routes(app)
user_routes(app)

# Create database and default admin
with app.app_context():
    db.create_all()
    migrate_booking_history_schema()

    admin = User.query.filter_by(role='admin').first()

    if not admin:
        admin_user = User(
            name='Admin',
            email="admin@gmail.com",
            password=generate_password_hash("admin123"),
            role='admin',
            status='active'
        )
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created successfully.")

# Redis connection test
print("Redis connection:", redis_client.ping())

if __name__ == "__main__":
    app.run(debug=True)
