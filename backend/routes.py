from flask import Flask, jsonify, request, session, send_file
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, StaffProfile, Trek, TrekAssignment, Booking
import redis, json
from celery_app import export_bookings_csv
import os

TREK_STATUSES = ["Pending", "Approved", "Open", "Closed", "Completed"]

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

def admin_required():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({
            "message": "Please login first."
        }), 401

    user = User.query.get(user_id)
    if not user or user.status != "active":
        session.clear()
        return jsonify({
            "message": "Your account is not active."
        }), 401

    if user.role != "admin" or session.get("user_role") != "admin":
        return jsonify({
            "message": "Admin access required."
        }), 403
    return None

def staff_required():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"message": "Please Login First"}), 401

    user = User.query.get(user_id)
    if not user or user.status != "active":
        session.clear()
        return jsonify({"message": "Your account is not active"}), 401

    if user.role != "staff" or session.get("user_role") != "staff":
        return jsonify({
            "message": "Staff access required."
        }), 403
    return None

def user_required():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"message": "Please Login First"}), 401

    user = User.query.get(user_id)
    if not user or user.status != "active":
        session.clear()
        return jsonify({"message": "Your account is not active"}), 401

    if user.role != "user" or session.get("user_role") != "user":
        return jsonify({
            "message": "User access required."
        }), 403
    return None

def authentication_routes(app):

    # Home route
    @app.route("/")
    def home():
        return jsonify({
            "message": "Trekking Management Application is running successfully!"
        })

    # Register route
    @app.route("/api/register", methods=["POST"])
    def register():
        data = request.get_json()
        name = data.get("name")
        email = data.get("email")
        password = data.get("password")
        phone_number = data.get("phone_number")

        if not name or not email or not password:
            return jsonify({"error": "Name, email, and password are required."}), 400

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({"error": "User with this email already exists."}), 400

        new_user = User(
            name=name,
            email=email, 
            password=generate_password_hash(password), 
            role="user", 
            phone_number=phone_number,
            status="active"
            )

        db.session.add(new_user)
        db.session.commit()

        return jsonify({
            "message": "User registered successfully."
            }), 201

    # Login route
    @app.route("/api/login", methods=["POST"])
    def login():
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({
                "error": "Email and password are required."
            }), 400

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            return jsonify({
                "error": "Invalid email or password."
                }), 401

        if user.status != "active":
            return jsonify({
                "error": "Your account is not active."
                }), 403

        session['user_id'] = user.id
        session['user_role'] = user.role 

        return jsonify({
            "message": "Login successful.", 
            "user": {
                "id": user.id, 
                "name": user.name, 
                "email": user.email, 
                "role": user.role
                }
            }), 200


    # Logout route
    @app.route("/api/logout", methods=["POST"])
    def logout():
        session.clear()

        return jsonify({
            "message": "Logout successful"
        })

    @app.route('/api/auth/check', methods=['GET'])
    def check_auth():
        user_id = session.get('user_id')
        user_role = session.get('user_role')

        if not user_id or not user_role:
            return jsonify({
                'authenticated': False
            }), 401

        user = User.query.get(user_id)

        if not user or user.status != 'active':
            session.clear()
            return jsonify({
                'authenticated': False
            }), 401

        return jsonify({
            'authenticated': True,
            'role': user.role
        }), 200

def admin_routes(app):
     
    # Admin route to create a new trek
    @app.route("/api/admin/treks", methods=["POST"])
    def create_trek():
        auth_response = admin_required()
        if auth_response:
            return auth_response

        data = request.get_json()

        name = data.get("name")
        location = data.get("location")
        description = data.get("description")
        duration = data.get("duration")
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        difficulty_level = data.get("difficulty_level") 
        available_slots = data.get("available_slots")

        if not name or not location or not duration or not start_date or not end_date or not difficulty_level or available_slots is None or not description:
            return jsonify({
                "error": "Required trek details are missing"
            }), 400

        if difficulty_level not in ["Easy", "Moderate", "Hard"]:
            return jsonify({
                "error": "Difficulty level must be one of: Easy, Moderate, Hard."
            }), 400

        if available_slots is None or available_slots < 0:
            return jsonify({
                "message": "Available slots must be 0 or more"
            }), 400

        from datetime import datetime

        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({
                "error": "Start date and end date must be in YYYY-MM-DD format."
            }), 400

        if start_date_obj >= end_date_obj:
            return jsonify({
                "error": "Start date must be before end date."
            }), 400

        trek = Trek(
            name=name,
            location=location,
            description=description,
            duration=duration,
            start_date=start_date_obj,
            end_date=end_date_obj,
            difficulty_level=difficulty_level,
            available_slots=available_slots
        )
        db.session.add(trek)
        db.session.commit()

        return jsonify({
            "message": "Trek created successfully.",
            "trek_id": trek.id
        }), 201

    # Admin route to view all treks
    @app.route("/api/admin/treks", methods=["GET"])
    def get_treks():
        auth_response = admin_required()

        if auth_response:
            return auth_response

        treks = Trek.query.all()
        treks_list = []

        for trek in treks:
            assignments = TrekAssignment.query.filter_by(
                trek_id=trek.id
            ).all()
            assigned_staff = []

            for assignment in assignments:
                staff = StaffProfile.query.get(assignment.staff_id)
                user = User.query.get(staff.user_id) if staff else None

                if staff and user:
                    assigned_staff.append({
                        "staff_id": staff.id,
                        "employee_id": staff.employee_id,
                        "name": user.name
                    })

            treks_list.append({
                "id": trek.id,
                "name": trek.name,
                "location": trek.location,
                "description": trek.description,
                "duration": trek.duration,
                "start_date": trek.start_date.strftime("%Y-%m-%d"),
                "end_date": trek.end_date.strftime("%Y-%m-%d"),
                "difficulty_level": trek.difficulty_level,
                "available_slots": trek.available_slots,
                "status": trek.status,
                "assigned_staff": assigned_staff
            })
        return jsonify({
            "treks": treks_list
            }), 200

    # Admin route to update trek details
    @app.route("/api/admin/treks/<int:id>", methods=["PUT"])
    def update_trek(id):
        auth_response = admin_required()
        if auth_response:
            return auth_response

        trek = Trek.query.get(id)
        if not trek:
            return jsonify({
                "error": "Trek not found."
            }), 404

        data = request.get_json()

        if "name" in data:
            trek.name = data["name"]

        if "location" in data:
            trek.location = data["location"]

        if "difficulty_level" in data:
            if data["difficulty_level"] not in ["Easy", "Moderate", "Hard"]:
                return jsonify({
                    "message": "Difficulty must be Easy, Moderate or Hard"
                }), 400

            trek.difficulty_level = data["difficulty_level"]

        if "duration" in data:
            trek.duration = data["duration"]

        if "available_slots" in data:
            if data["available_slots"] < 0:
                return jsonify({
                    "message": "Available slots must be 0 or more"
                }), 400

            trek.available_slots = data["available_slots"]

        if "status" in data:
            if data["status"] not in TREK_STATUSES:
                return jsonify({
                    "message": "Invalid trek status"
                }), 400

            trek.status = data["status"]

        if "start_date" in data:
            from datetime import datetime

            try:
                trek.start_date = datetime.strptime(
                    data["start_date"], "%Y-%m-%d"
                ).date()

            except ValueError:
                return jsonify({
                    "message": "Start date must be in YYYY-MM-DD format"
                }), 400

        if "end_date" in data:
            from datetime import datetime

            try:
                trek.end_date = datetime.strptime(
                    data["end_date"], "%Y-%m-%d"
                ).date()

            except ValueError:
                return jsonify({
                    "message": "End date must be in YYYY-MM-DD format"
                }), 400

        if trek.end_date < trek.start_date:
            return jsonify({
                "message": "End date cannot be before start date"
            }), 400

        if "description" in data:
            trek.description = data["description"]

        db.session.commit()
        redis_client.delete("open_treks")

        return jsonify({
            "message": "Trek updated successfully"
        }), 200

    # Admin route to delete a trek
    @app.route("/api/admin/treks/<int:id>", methods=["DELETE"])
    def delete_trek(id):
        auth_response = admin_required()
        if auth_response:
            return auth_response

        trek = Trek.query.get(id)
        if not trek:
            return jsonify({
                "error": "Trek not found."
            }), 404

        db.session.delete(trek)
        db.session.commit()
        redis_client.delete("open_treks")
        
        return jsonify({
            "message": "Trek deleted successfully."
        }), 200

    # Admin route to create a new staff profile
    @app.route("/api/admin/staff", methods=["POST"])
    def create_staff():
        auth_response = admin_required()
        if auth_response:
            return auth_response

        data = request.get_json() or {}

        name = data.get("name")
        email = data.get("email")
        password = data.get("password")
        phone_number = data.get("phone_number")
        designation = data.get("designation")

        if not name or not email or not password:
            return jsonify({
                "error": "Name, email, and password are required."
            }), 400

        # Check whether email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({
                "error": "User with this email already exists."
            }), 400

        # Create staff login account
        staff_user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role="staff",
            phone_number=phone_number,
            status="active"
        )

        db.session.add(staff_user)
        db.session.flush()

        # Generate Employee ID automatically
        employee_id = f"EMP{staff_user.id:03d}"

        # Today's date is assigned automatically
        from datetime import date

        staff_profile = StaffProfile(
            user_id=staff_user.id,
            employee_id=employee_id,
            designation=designation,
            joining_date=date.today()
        )

        db.session.add(staff_profile)
        db.session.commit()

        return jsonify({
            "message": "Staff profile created successfully.",
            "staff_id": staff_profile.id,
            "user_id": staff_user.id,
            "employee_id": staff_profile.employee_id,
            "joining_date": staff_profile.joining_date.strftime("%Y-%m-%d")
        }), 201



    # Admin route to view all staff profiles
    @app.route("/api/admin/staff", methods=["GET"])
    def get_staff_profiles():
        auth_response = admin_required()
        if auth_response:
            return auth_response

        staff_profiles = StaffProfile.query.all()
        staff_list = []

        for staff in staff_profiles:
            user = User.query.get(staff.user_id)
            staff_list.append({
                "id": staff.id,
                "user_id": user.id,
                "name": user.name,
                "email": user.email,
                "phone_number": user.phone_number,
                "employee_id": staff.employee_id,
                "designation": staff.designation,
                "joining_date": staff.joining_date.strftime("%Y-%m-%d") if staff.joining_date else None,
                "created_at": staff.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "status": user.status
            })

        return jsonify({
            "staff_profiles": staff_list
        }), 200


    # Admin route to assign a staff member to a trek
    @app.route("/api/admin/treks/<int:trek_id>/assign-staff", methods=["POST"])
    def assign_staff(trek_id):
        auth_response = admin_required()

        if auth_response:
            return auth_response

        data = request.get_json()

        staff_id = data.get("staff_id")

        if not staff_id:
            return jsonify({
                "error": "Staff ID is required."
            }), 400

        trek = Trek.query.get(trek_id)

        if not trek:
            return jsonify({
                "error": "Trek not found."
            }), 404

        staff = StaffProfile.query.get(staff_id)

        if not staff:
            return jsonify({
                "error": "Staff not found."
            }), 404

        existing_assignment = TrekAssignment.query.filter_by(
            trek_id=trek_id,
            staff_id=staff_id
        ).first()

        if existing_assignment:
            return jsonify({
                "error": "Staff is already assigned to this trek."
            }), 400

        assignment = TrekAssignment(
            trek_id=trek_id,
            staff_id=staff_id
        )

        db.session.add(assignment)
        db.session.commit()

        return jsonify({
            "message": "Staff assigned to trek successfully."
        }), 201

    # Admin route to view all trek assignments
    @app.route("/api/admin/treks/<int:trek_id>/staff", methods=["GET"])
    def get_trek_staff(trek_id):
        auth_response = admin_required()

        if auth_response:
            return auth_response

        trek = Trek.query.get(trek_id)

        if not trek:
            return jsonify({
                "error": "Trek not found."
            }), 404

        assignments = TrekAssignment.query.filter_by(
            trek_id=trek_id
        ).all()

        staff_list = []

        for assignment in assignments:
            staff = StaffProfile.query.get(assignment.staff_id)
            user = User.query.get(staff.user_id)

            staff_list.append({
                "staff_id": staff.id,
                "employee_id": staff.employee_id,
                "name": user.name,
                "email": user.email,
                "phone_number": user.phone_number,
                "designation": staff.designation,
                "status": user.status
            })

        return jsonify({
            "trek_id": trek.id,
            "trek_name": trek.name,
            "staff": staff_list
        }), 200


    # Admin route to view all users
    @app.route("/api/admin/users", methods=["GET"])
    def get_users():
        auth_response = admin_required()

        if auth_response:
            return auth_response

        users = User.query.filter(User.role != "admin").all()

        users_list = []

        for user in users:
            users_list.append({
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "phone_number": user.phone_number,
                "status": user.status,
                "role": user.role,
                "created_at": user.created_at.strftime("%Y-%m-%d")
            })

        return jsonify({
            "users": users_list
        }), 200

    # Admin route to Deactivate/Activate User
    @app.route("/api/admin/users/<int:user_id>/status", methods=["PUT"])
    def update_user_status(user_id):
        auth_response = admin_required()

        if auth_response:
            return auth_response

        user = User.query.filter_by(
            id=user_id,
            role="user"
        ).first()

        if not user:
            return jsonify({
                "error": "User not found."
            }), 404

        data = request.get_json()
        status = data.get("status")

        if status not in ["active", "inactive", "blacklisted"]:
            return jsonify({
                "error": "Status must be active, inactive or blacklisted."
            }), 400

        user.status = status

        db.session.commit()

        return jsonify({
            "message": "User status updated successfully.",
            "user_id": user.id,
            "status": user.status
        }), 200

    # Admin Route to view all bookings
    @app.route("/api/admin/bookings", methods=["GET"])
    def get_all_bookings():
        auth_response = admin_required()

        if auth_response:
            return auth_response

        bookings = Booking.query.all()

        bookings_list = []

        for booking in bookings:
            user = User.query.get(booking.user_id)
            trek = Trek.query.get(booking.trek_id)

            if user and trek:
                bookings_list.append({
                    "booking_id": booking.id,
                    "user_id": user.id,
                    "user_name": user.name,
                    "user_email": user.email,
                    "trek_id": trek.id,
                    "trek_name": trek.name,
                    "booking_date": booking.booking_date.strftime("%Y-%m-%d"),
                    "status": booking.status
                })

        return jsonify({
            "bookings": bookings_list
        }), 200

    # Admin route to manage booking status
    @app.route("/api/admin/bookings/<int:booking_id>/status", methods=["PUT"])
    def update_booking_status(booking_id):
        auth_response = admin_required()

        if auth_response:
            return auth_response

        booking = Booking.query.get(booking_id)

        if not booking:
            return jsonify({
                "error": "Booking not found."
            }), 404

        data = request.get_json()
        status = data.get("status")

        if status not in ["Booked", "Cancelled", "Completed"]:
            return jsonify({
                "error": "Invalid booking status."
            }), 400

        booking.status = status

        db.session.commit()

        return jsonify({
            "message": "Booking status updated successfully.",
            "booking_id": booking.id,
            "status": booking.status
        }), 200

    # Admin Route to Deactivate/Activate Staff 
    @app.route("/api/admin/staff/<int:staff_id>/status", methods=["PUT"])
    def update_staff_status(staff_id):
        auth_response = admin_required()

        if auth_response:
            return auth_response

        staff = StaffProfile.query.get(staff_id)

        if not staff:
            return jsonify({
                "error": "Staff not found."
            }), 404

        user = User.query.get(staff.user_id)

        if not user:
            return jsonify({
                "error": "Staff user account not found."
            }), 404

        data = request.get_json()
        status = data.get("status")

        if status not in ["active", "inactive", "blacklisted"]:
            return jsonify({
                "error": "Status must be active, inactive or blacklisted."
            }), 400

        user.status = status

        db.session.commit()

        return jsonify({
            "message": "Staff status updated successfully.",
            "staff_id": staff.id,
            "status": user.status
        }), 200

    
    # Admin Route for Dashboard Statistics
    @app.route("/api/admin/statistics", methods=["GET"])
    def get_admin_statistics():
        auth_response = admin_required()
        if auth_response:
            return auth_response

        total_users = User.query.filter_by(role="user").count()
        total_staff = User.query.filter_by(role="staff").count()
        total_treks = Trek.query.count()
        total_bookings = Booking.query.count()

        return jsonify({
            "total_users": total_users,
            "total_staff": total_staff,
            "total_treks": total_treks,
            "total_bookings": total_bookings
        }), 200

    # Starts CSV export in background
    @app.route("/api/admin/bookings/export", methods=["POST"])
    def start_bookings_export():
        auth_response = admin_required()
        if auth_response:
            return auth_response

        task = export_bookings_csv.delay()

        return jsonify({
            "message": "CSV export started successfully.",
            "task_id": task.id
        }), 202

    # Check CSV export task status 
    @app.route("/api/admin/bookings/export/<task_id>", methods=["GET"])
    def check_booking_export(task_id):
        auth_response = admin_required()
        if auth_response:
            return auth_response

        from celery_app import celery

        task = celery.AsyncResult(task_id)

        result = {
            "task_id": task_id,
            "status": task.status
        }

        if task.successful():
            result["message"] = "CSV export completed."
            result["download_url"] = (
                f"/api/admin/bookings/export/{task_id}/download"
            )
        elif task.failed():
            result["message"] = "CSV export failed."

        return jsonify(result), 200

    # Download completed CSV securely
    @app.route("/api/admin/bookings/export/<task_id>/download",methods=["GET"])
    def download_bookings_export(task_id):
        auth_response = admin_required()
        if auth_response:
            return auth_response

        from celery_app import celery

        task = celery.AsyncResult(task_id)

        if not task.successful():
            return jsonify({
                "error": "Export is not completed yet."
            }), 400

        result = task.result

        if not isinstance(result, dict):
            return jsonify({
                "error": "Invalid export result."
            }), 404

        file_path = result.get("file_path")

        export_folder = os.path.realpath(
            os.path.join(app.root_path, "exports")
        )

        if not file_path or not os.path.isfile(file_path):
            return jsonify({
                "error": "Export file not found."
            }), 404

        file_path = os.path.realpath(file_path)

        if os.path.commonpath([export_folder, file_path]) != export_folder:
            return jsonify({
                "error": "Invalid export file path."
            }), 403

        return send_file(
            file_path,
            as_attachment=True,
            download_name="bookings.csv",
            mimetype="text/csv"
        )

    
    # Start Monthly Report background task
    @app.route("/api/admin/monthly-report", methods=["POST"])
    def start_monthly_report():
        auth_response = admin_required()
        if auth_response:
            return auth_response

        from celery_app import generate_monthly_report

        task = generate_monthly_report.delay()

        return jsonify({
            "message": "Monthly report generation started.",
            "task_id": task.id
        }), 202

    # Check Monthly Report status and result
    @app.route("/api/admin/monthly-report/<task_id>", methods=["GET"])
    def get_monthly_report_status(task_id):
        auth_response = admin_required()
        if auth_response:
            return auth_response

        from celery_app import celery

        task = celery.AsyncResult(task_id)

        result = {
            "task_id": task_id,
            "status": task.status
        }

        if task.successful():
            result["message"] = "Monthly report generated successfully."
            result["report"] = task.result

        elif task.failed():
            result["message"] = "Monthly report generation failed."

        return jsonify(result), 200

    # Start Booking Reminders
    @app.route("/api/admin/booking-reminders", methods=["POST"])
    def start_booking_reminders():
        auth_response = admin_required()
        if auth_response:
            return auth_response

        from celery_app import send_booking_reminders

        task = send_booking_reminders.delay()

        return jsonify({
            "message": "Booking reminders started.",
            "task_id": task.id
        }), 202

    # Get Status of booking reminders
    @app.route("/api/admin/booking-reminders/<task_id>", methods=["GET"])
    def get_booking_reminders_status(task_id):
        auth_response = admin_required()
        if auth_response:
            return auth_response

        from celery_app import celery

        task = celery.AsyncResult(task_id)

        result = {
            "task_id": task_id,
            "status": task.status
        }

        if task.successful():
            result["message"] = "Booking reminders generated successfully."
            result["report"] = task.result
        elif task.failed():
            result["message"] = "Booking reminder generation failed."

        return jsonify(result), 200

def staff_routes(app):

    # Staff route to view assigned treks
    @app.route("/api/staff/treks", methods=["GET"])
    def get_assigned_treks():
        auth_response = staff_required()
        if auth_response:
            return auth_response

        user_id = session.get("user_id")
        staff = StaffProfile.query.filter_by(user_id=user_id).first()

        if not staff:
            return jsonify({
                "error": "Staff profile not found."
            }), 404

        assignments = TrekAssignment.query.filter_by(staff_id=staff.id).all()

        treks_list = []

        for assignment in assignments:
            trek = Trek.query.get(assignment.trek_id)
            registered_user_count = Booking.query.filter_by(
                trek_id=trek.id
            ).filter(
                Booking.status != "Cancelled"
            ).count()
            treks_list.append({
                "id": trek.id,
                "name": trek.name,
                "location": trek.location,
                "description": trek.description,
                "duration": trek.duration,
                "start_date": trek.start_date.strftime("%Y-%m-%d"),
                "end_date": trek.end_date.strftime("%Y-%m-%d"),
                "difficulty_level": trek.difficulty_level,
                "available_slots": trek.available_slots,
                "status": trek.status,
                "registered_user_count": registered_user_count
            })

        return jsonify({
            "staff_id": staff.id,
            "employee_id": staff.employee_id,
            "treks": treks_list
        }), 200

    @app.route("/api/staff/registered-users", methods=["GET"])
    def get_registered_users():
        auth_response = staff_required()
        if auth_response:
            return auth_response

        staff = StaffProfile.query.filter_by(
            user_id=session.get("user_id")
        ).first()

        if not staff:
            return jsonify({
                "error": "Staff profile not found."
            }), 404

        assignments = TrekAssignment.query.filter_by(staff_id=staff.id).all()
        assigned_trek_ids = [assignment.trek_id for assignment in assignments]
        bookings = Booking.query.filter(
            Booking.trek_id.in_(assigned_trek_ids)
        ).all() if assigned_trek_ids else []

        users_list = []
        for booking in bookings:
            user = User.query.get(booking.user_id)
            trek = Trek.query.get(booking.trek_id)

            if user and trek:
                users_list.append({
                    "user_id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "phone_number": user.phone_number,
                    "booking_id": booking.id,
                    "trek_name": trek.name,
                    "booking_status": booking.status
                })

        return jsonify({"users": users_list}), 200

    # Staff route to view bookings for assigned treks
    @app.route("/api/staff/treks/<int:trek_id>/users", methods=["GET"])
    def get_trek_users(trek_id):
        auth_response = staff_required()
        if auth_response:
            return auth_response

        user_id = session.get("user_id")
        staff = StaffProfile.query.filter_by(
            user_id=user_id
        ).first()

        if not staff:
            return jsonify({
                "error": "Staff profile not found."
            }), 404

        assignment = TrekAssignment.query.filter_by(
            trek_id=trek_id,
            staff_id=staff.id
        ).first()

        if not assignment:
            return jsonify({
                "error": "You are not assigned to this trek."
            }), 403

        trek = Trek.query.get(trek_id)

        if not trek:
            return jsonify({
                "error": "Trek not found."
            }), 404

        bookings = Booking.query.filter_by(
            trek_id=trek_id
        ).all()

        users_list = []

        for booking in bookings:
            user = User.query.get(booking.user_id)

            if user:
                users_list.append({
                    "user_id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "phone_number": user.phone_number,
                    "booking_id": booking.id,
                    "booking_status": booking.status
                })

        return jsonify({
            "trek_id": trek.id,
            "trek_name": trek.name,
            "users": users_list
        }), 200

    # Staff route to update booking status and available slots for assigned treks
    @app.route("/api/staff/treks/<int:trek_id>", methods=["PUT"])
    def update_staff_trek(trek_id):
        auth_response = staff_required()
        if auth_response:
            return auth_response

        user_id = session.get("user_id")
        staff = StaffProfile.query.filter_by(user_id=user_id).first()

        if not staff:
            return jsonify({
                "error": "Staff profile not found."
            }), 404

        assignment = TrekAssignment.query.filter_by(
            trek_id=trek_id,
            staff_id=staff.id
        ).first()
        if not assignment:
            return jsonify({
                "error": "You are not assigned to this trek."
            }), 403

        trek = Trek.query.get(trek_id)
        if not trek:
            return jsonify({
                "error": "Trek not found."
            }), 404

        data = request.get_json()

        if "available_slots" in data:
            if data["available_slots"] < 0:
                return jsonify({
                    "error": "Available slots must be 0 or more."
                }), 400

            trek.available_slots = data["available_slots"]

        if "status" in data:
            if data["status"] not in TREK_STATUSES:
                return jsonify({
                    "error": "Invalid trek status."
                }), 400

            trek.status = data["status"]

        db.session.commit()
        redis_client.delete("open_treks")

        return jsonify({
            "message": "Trek updated successfully."
        }), 200

def user_routes(app):

    # User route to view profile
    @app.route("/api/user/profile", methods=["GET"])
    def profile():
        auth_response = user_required()
        if auth_response:
            return auth_response
        
        if "user_id" not in session:
            return jsonify({
                "message": "Please login first."
            })

        user_id = session.get("user_id")
        user = User.query.get(user_id)

        if not user:
            return jsonify({
                "error": "User not found."
            }), 404

        return jsonify({
            "id":user.id,
            "name":user.name,
            "email":user.email,
            "phone_number":user.phone_number,
            "role":user.role,
            "status":user.status
        }), 200

    @app.route("/api/user/profile", methods=["PUT"])
    def update_profile():
        auth_response = user_required()
        if auth_response:
            return auth_response

        user = User.query.get(session.get("user_id"))
        if not user:
            return jsonify({"error": "User not found."}), 404

        data = request.get_json() or {}
        name = data.get("name", "").strip()
        email = data.get("email", "").strip()
        phone_number = data.get("phone_number", "").strip()
        password = data.get("password", "").strip()

        if not name or not email:
            return jsonify({
                "error": "Name and email are required."
            }), 400

        existing_user = User.query.filter(
            User.email == email,
            User.id != user.id
        ).first()
        if existing_user:
            return jsonify({
                "error": "User with this email already exists."
            }), 400

        user.name = name
        user.email = email
        user.phone_number = phone_number or None

        if password:
            user.password = generate_password_hash(password)

        db.session.commit()

        return jsonify({
            "message": "Profile updated successfully.",
            "name": user.name,
            "email": user.email,
            "phone_number": user.phone_number
        }), 200

    # User route to view all available treks
    @app.route("/api/treks", methods=["GET"])
    def get_open_treks():
        auth_response = user_required()
        if auth_response:
            return auth_response

        cached_treks = redis_client.get("open_treks")

        if cached_treks:
            return jsonify({
                "treks": json.loads(cached_treks),
                "source": "cache"
            }), 200

        treks = Trek.query.filter(
            Trek.status == "Open",
            Trek.available_slots > 0
        ).all()

        treks_list = []

        for trek in treks:
            treks_list.append({
                "id": trek.id,
                "name": trek.name,
                "location": trek.location,
                "description": trek.description,
                "duration": trek.duration,
                "start_date": trek.start_date.strftime("%Y-%m-%d"),
                "end_date": trek.end_date.strftime("%Y-%m-%d"),
                "difficulty_level": trek.difficulty_level,
                "available_slots": trek.available_slots,
                "status": trek.status
            })

        redis_client.setex(
            "open_treks",
            60,
            json.dumps(treks_list)
        )

        return jsonify({
            "treks": treks_list,
            "source": "database"
        }), 200

    
    # User route to book a trek
    @app.route("/api/bookings", methods=["POST"])
    def create_booking():
        auth_response = user_required()
        if auth_response:
            return auth_response
        
        if "user_id" not in session:
            return jsonify({
                "message": "Please login first."
            }), 401

        user_id = session.get("user_id")

        data = request.get_json() or {}

        trek_id = data.get("trek_id")
        if not trek_id:
            return jsonify({
                "error": "Trek ID is required."
            }), 400

        trek = Trek.query.get(trek_id)

        if not trek:
            return jsonify({
                "error": "Trek not found."
            }), 404

        if trek.status != "Open":
            return jsonify({
                "error": "Trek is not open for booking."
            }), 400

        if trek.available_slots <= 0:
            return jsonify({
                "error": "No available slots for this trek."
            }), 400

        existing_booking = Booking.query.filter_by(
            user_id=user_id,
            trek_id=trek_id
        ).filter(
            Booking.status != "Cancelled"
        ).first()

        # Reject duplicate active bookings
        if existing_booking:
            return jsonify({
                "error": "You have already booked this trek."
            }), 400

        # Create a new row so cancelled bookings remain in the history.
        booking = Booking(
            user_id=user_id,
            trek_id=trek_id,
            status="Booked"
        )

        trek.available_slots -= 1

        db.session.add(booking)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return jsonify({
                "error": "You have already booked this trek."
            }), 400

        redis_client.delete("open_treks")

        return jsonify({
            "message": "Trek booked successfully.",
            "booking_id": booking.id,
            "trek_id": trek.id,
            "remaining_slots": trek.available_slots
        }), 201



    # User route to view user's bookings
    @app.route("/api/bookings", methods=["GET"])
    def get_my_bookings():
        auth_response = user_required()
        if auth_response:
            return auth_response
        
        if "user_id" not in session:
            return jsonify({
                "message": "Please login first."
            }), 401

        user_id = session.get("user_id")

        bookings = Booking.query.filter_by(
            user_id=user_id
        ).all()

        bookings_list = []

        for booking in bookings:
            trek = Trek.query.get(booking.trek_id)

            if trek:
                bookings_list.append({
                    "booking_id": booking.id,
                    "trek_id": trek.id,
                    "trek_name": trek.name,
                    "location": trek.location,
                    "start_date": trek.start_date.strftime("%Y-%m-%d"),
                    "end_date": trek.end_date.strftime("%Y-%m-%d"),
                    "booking_date": booking.booking_date.strftime("%Y-%m-%d"),
                    "status": booking.status                  
                })

        return jsonify({
            "bookings": bookings_list
        }), 200

    # User Route to update booking
    @app.route("/api/bookings/<int:booking_id>/cancel", methods=["PUT"])
    def cancel_booking(booking_id):
        auth_response = user_required()
        if auth_response:
            return auth_response

        if "user_id" not in session:
            return jsonify({
                "message": "Please login first."
            }), 401

        user_id = session.get("user_id")

        booking = Booking.query.get(booking_id)
        if not booking:
            return jsonify({
                "error": "Booking not found."
            }), 404

        if booking.user_id != user_id:
            return jsonify({
                "error": "You can only cancel your own booking."
            }), 403

        if booking.status == "Cancelled":
            return jsonify({
                "error": "Booking is already cancelled."
            }), 400

        if booking.status == "Completed":
            return jsonify({
                "error": "Completed booking cannot be cancelled."
            }), 400

        trek = Trek.query.get(booking.trek_id)

        if not trek:
            return jsonify({
                "error": "Trek not found."
            }), 404

        booking.status = "Cancelled"
        trek.available_slots += 1

        db.session.commit()
        redis_client.delete("open_treks")

        return jsonify({
            "message": "Booking cancelled successfully.",
            "booking_id": booking.id,
            "status": booking.status,
            "available_slots": trek.available_slots
        }), 200

    
    # User route to start personal CSV export
    @app.route("/api/user/export-bookings", methods=["POST"])
    def start_user_csv_export():
        auth_response = user_required()
        if auth_response:
            return auth_response

        user_id = session.get("user_id")

        if not user_id:
            return jsonify({"message": "Please login first."}), 401

        from celery_app import export_user_bookings_csv

        task = export_user_bookings_csv.delay(user_id)

        # Store task ownership in Redis for 1 day
        redis_client.setex(
            f"user_csv:{task.id}",
            86400,
            str(user_id)
        )

        return jsonify({
            "message": "Your CSV export has started.",
            "task_id": task.id
        }), 202


    # User route to check CSV export status
    @app.route("/api/user/export-bookings/<task_id>", methods=["GET"])
    def user_csv_export_status(task_id):
        auth_response = user_required()
        if auth_response:
            return auth_response

        user_id = session.get("user_id")

        task_owner = redis_client.get(f"user_csv:{task_id}")

        if not task_owner or task_owner != str(user_id):
            return jsonify({
                "error": "Export not found or access denied."
            }), 404

        from celery_app import celery

        task = celery.AsyncResult(task_id)

        response = {
            "task_id": task_id,
            "status": task.status
        }

        if task.successful():
            response["message"] = "CSV export completed."
            response["email_sent"] = task.result.get(
                "email_sent", False
            )

        elif task.failed():
            response["message"] = "CSV export failed."

        return jsonify(response), 200


    # User route to download their CSV
    @app.route("/api/user/export-bookings/<task_id>/download", methods=["GET"])
    def download_user_csv(task_id):
        auth_response = user_required()
        if auth_response:
            return auth_response

        user_id = session.get("user_id")

        task_owner = redis_client.get(f"user_csv:{task_id}")

        if not task_owner or task_owner != str(user_id):
            return jsonify({
                "error": "Export not found or access denied."
            }), 404

        from celery_app import celery
        from flask import send_file

        task = celery.AsyncResult(task_id)

        if not task.successful():
            return jsonify({
                "error": "CSV export is not ready yet."
            }), 400

        file_path = task.result.get("file_path")

        if not file_path or not os.path.isfile(file_path):
            return jsonify({
                "error": "CSV file not found."
            }), 404

        return send_file(
            file_path,
            as_attachment=True,
            download_name="my_trekking_history.csv",
            mimetype="text/csv"
        )


    
    
