from celery import Celery
from celery.schedules import crontab
from datetime import date, timedelta
from models import db, User, Trek, Booking
from flask_mail import Message
import csv
import os


celery = Celery(
    "tma",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)

celery.conf.timezone = "Asia/Kolkata"

celery.conf.beat_schedule = {
    "daily-booking-reminders": {
        "task": "celery_app.send_booking_reminders",
        "schedule": crontab(hour=9, minute=0),
    },
    "monthly-trekking-report": {
        "task": "celery_app.generate_monthly_report",
        "schedule": crontab(
            day_of_month=1,
            hour=9,
            minute=0
        ),
    },
}

@celery.task
def send_booking_reminders():
    import app

    with app.app.app_context():
        today = date.today()
        last_date = today + timedelta(days=3)

        bookings = (
            Booking.query
            .join(Trek, Booking.trek_id == Trek.id)
            .filter(
                Trek.start_date > today,
                Trek.start_date <= last_date,
                Booking.status.notin_(["Cancelled", "Completed"]),
                Booking.reminder_sent == False
            )
            .all()
        )

        reminder_count = 0
        emails_sent = 0
        emails_failed = 0

        for booking in bookings:
            user = User.query.get(booking.user_id)
            trek = Trek.query.get(booking.trek_id)

            if user and trek:
                reminder_count += 1

                print("\n--- BOOKING REMINDER ---")
                print(f"User: {user.name}")
                print(f"Email: {user.email}")
                print(f"Trek: {trek.name}")
                print(f"Start Date: {trek.start_date}")
                print("------------------------\n")

                try:
                    message = Message(
                        subject="Upcoming Trek Booking Reminder",
                        recipients=[user.email],
                        body=f"""
                            Hello {user.name},

                            This is a reminder about your upcoming trekking booking.

                            Trek Name: {trek.name}
                            Location: {trek.location}
                            Start Date: {trek.start_date}
                            End Date: {trek.end_date}

                            Please make sure you are prepared for your trek.

                            Thank you,
                            Trekking Management Application
                            """
                    )

                    app.mail.send(message)
                    booking.reminder_sent = True
                    db.session.commit()
                    emails_sent += 1

                    print(f"Reminder email sent to {user.email}")

                except Exception as error:
                    emails_failed += 1
                    print(f"Failed to send email to {user.email}: {error}")

        print(f"Total reminders generated: {reminder_count}")
        print(f"Emails sent: {emails_sent}")
        print(f"Emails failed: {emails_failed}")

        return {
            "reminders_generated": reminder_count,
            "emails_sent": emails_sent,
            "emails_failed": emails_failed,
            "checked_on": str(today)
        }



@celery.task
def generate_monthly_report():
    import app
    from sqlalchemy import func
    from datetime import date
    from flask_mail import Message

    with app.app.app_context():

        # Get the current month's date range
        today = date.today()
        first_day = today.replace(day=1)

        if first_day.month == 12:
            next_month = first_day.replace(
                year=first_day.year + 1,
                month=1
            )
        else:
            next_month = first_day.replace(
                month=first_day.month + 1
            )

        # Total bookings created this month
        total_bookings = Booking.query.filter(
            Booking.created_at >= first_day,
            Booking.created_at < next_month
        ).count()

        # Completed bookings this month
        completed_bookings = Booking.query.filter(
            Booking.created_at >= first_day,
            Booking.created_at < next_month,
            Booking.status == "Completed"
        ).count()

        # Cancelled bookings this month
        cancelled_bookings = Booking.query.filter(
            Booking.created_at >= first_day,
            Booking.created_at < next_month,
            Booking.status == "Cancelled"
        ).count()

        # Treks conducted this month
        total_treks = Trek.query.filter(
            Trek.start_date >= first_day,
            Trek.start_date < next_month
        ).count()

        # Total unique participants in completed treks
        total_participants = (
            db.session.query(func.count(func.distinct(Booking.user_id)))
            .join(Trek, Booking.trek_id == Trek.id)
            .filter(
                Trek.start_date >= first_day,
                Trek.start_date < next_month,
                Booking.status == "Completed"
            )
            .scalar()
        )

        # Find the five most popular treks this month
        popular_treks = (
            db.session.query(
                Trek.name,
                func.count(Booking.id).label("booking_count")
            )
            .join(Booking, Booking.trek_id == Trek.id)
            .filter(
                Booking.created_at >= first_day,
                Booking.created_at < next_month
            )
            .group_by(Trek.id, Trek.name)
            .order_by(func.count(Booking.id).desc())
            .limit(5)
            .all()
        )

        # Prepare report data
        report = {
            "month": first_day.strftime("%B %Y"),
            "total_bookings": total_bookings,
            "completed_bookings": completed_bookings,
            "cancelled_bookings": cancelled_bookings,
            "total_treks": total_treks,
            "total_participants": total_participants,
            "popular_treks": [
                {
                    "trek_name": trek_name,
                    "bookings": booking_count
                }
                for trek_name, booking_count in popular_treks
            ]
        }

        print("MONTHLY TREKKING REPORT:", report)

        # Find Admin
        admin = User.query.filter_by(role="admin").first()

        # Send report email
        if admin and admin.email:

            popular_treks_text = ""

            if popular_treks:
                for index, (trek_name, booking_count) in enumerate(
                    popular_treks, start=1
                ):
                    popular_treks_text += (
                        f"{index}. {trek_name} - "
                        f"{booking_count} bookings\n"
                    )
            else:
                popular_treks_text = "No popular treks this month."

            message = Message(
                subject=f"Monthly Trekking Report - {report['month']}",
                recipients=[admin.email],
                body=f"""
                    Hello Admin,

                    Here is your monthly trekking activity report.

                    Month: {report['month']}

                    TREKKING STATISTICS
                    -------------------------
                    Total Bookings: {total_bookings}
                    Completed Bookings: {completed_bookings}
                    Cancelled Bookings: {cancelled_bookings}
                    Treks Conducted: {total_treks}
                    Total Participants: {total_participants}

                    TOP 5 POPULAR TREKS
                    -------------------------
                    {popular_treks_text}

                    Thank you,
                    Trekking Management Application
                                    """
            )

            app.mail.send(message)
            print("Monthly report email sent to:", admin.email)

        else:
            print("Admin email not found. Report email not sent.")

        return report


@celery.task(bind=True)
def export_bookings_csv(self):
    import app
    from flask import current_app

    with app.app.app_context():
        export_folder = os.path.join(
            current_app.root_path, "exports"
        )
        os.makedirs(export_folder, exist_ok=True)

        file_path = os.path.join(
            export_folder, f"bookings_{self.request.id}.csv"
        )

        bookings = Booking.query.order_by(
            Booking.created_at.desc()
        ).all()

        with open(file_path, "w", newline="", encoding="utf-8-sig") as csv_file:
            writer = csv.writer(csv_file)

            writer.writerow([
                "Booking ID",
                "User ID",
                "Trek ID",
                "Booking Date",
                "Status"
            ])

            for booking in bookings:
                writer.writerow([
                    booking.id,
                    booking.user_id,
                    booking.trek_id,
                    booking.booking_date,
                    booking.status
                ])

        return {
            "message": "CSV export completed",
            "file_path": file_path
        }


@celery.task(bind=True)
def export_user_bookings_csv(self, user_id):
    import app
    from flask import current_app
    from flask_mail import Message

    with app.app.app_context():

        # Create exports folder
        export_folder = os.path.join(
            current_app.root_path, "exports"
        )
        os.makedirs(export_folder, exist_ok=True)

        # Create CSV file
        file_path = os.path.join(
            export_folder, f"user_bookings_{self.request.id}.csv"
        )

        # Get only this user's bookings
        bookings = Booking.query.filter_by(
            user_id=user_id
        ).order_by(Booking.created_at.desc()).all()

        with open(
            file_path, "w", newline="", encoding="utf-8-sig"
        ) as csv_file:

            writer = csv.writer(csv_file)

            writer.writerow([
                "User ID",
                "Trek Name",
                "Location",
                "Booking Status",
                "Booking Date",
                "Trek Start Date",
                "Trek End Date"
            ])

            for booking in bookings:
                trek = Trek.query.get(booking.trek_id)

                if trek:
                    writer.writerow([
                        booking.user_id,
                        trek.name,
                        trek.location,
                        booking.status,
                        booking.booking_date,
                        trek.start_date,
                        trek.end_date
                    ])

        # Notify user by email
        user = User.query.get(user_id)

        email_sent = False

        if user and user.email:
            try:
                message = Message(
                    subject="Your Trekking History CSV is Ready!",
                    recipients=[user.email],
                    body=f"""
                    Hello {user.name},

                    Your trekking history CSV export has been completed successfully.

                    You can log in to your Trekking Management Application
                    and download your CSV from the My Bookings section.

                    Thank you,
                    Trekking Management Application
                """
                )

                app.mail.send(message)
                email_sent = True

            except Exception as error:
                print("CSV notification email failed:", error)

        return {
            "message": "User CSV export completed.",
            "user_id": user_id,
            "file_path": file_path,
            "email_sent": email_sent
        }
