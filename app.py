import os
import threading
from pathlib import Path
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_mail import Mail, Message
from dotenv import load_dotenv
from models import db, Inquiry

# Explicitly load .env from the exact directory of app.py
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback_dev_key")

# Database Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{BASE_DIR / 'meridian.db'}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Email / SMTP Configuration
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = ("Meridian Inquiries", os.getenv("MAIL_USERNAME"))
# Set a strict 5-second socket timeout so connections never hang
app.config["MAIL_TIMEOUT"] = 5

# Initialize Extensions
db.init_app(app)
mail = Mail(app)

with app.app_context():
    db.create_all()


def send_async_email(app_instance, msg):
    """Sends email in a background thread without blocking the HTTP worker."""
    with app_instance.app_context():
        try:
            mail.send(msg)
            print("Email sent successfully in background.")
        except Exception as e:
            print(f"SMTP Background Dispatch Warning (often blocked on free hosting): {e}")


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message_body = request.form.get("message")

        # 1. Save inquiry immediately to SQLite database
        new_inquiry = Inquiry(name=name, email=email, message=message_body)
        db.session.add(new_inquiry)
        db.session.commit()

        # 2. Check credentials
        mail_user = os.getenv("MAIL_USERNAME")
        mail_pass = os.getenv("MAIL_PASSWORD")
        recipient_target = os.getenv("MAIL_RECEIVER") or mail_user

        if mail_user and mail_pass and recipient_target:
            # 3. Dispatch email in a non-blocking background thread
            msg = Message(
                subject=f"New Advisory Inquiry from {name}",
                recipients=[recipient_target],
                body=f"Name: {name}\nEmail: {email}\n\nMessage:\n{message_body}",
            )
            thr = threading.Thread(target=send_async_email, args=(app, msg))
            thr.daemon = True
            thr.start()

        flash(f"Thank you, {name}. Your inquiry has been received!", "success")
        return redirect(url_for("index") + "#contact")

    return render_template("index.html")


@app.route("/practice-areas")
def practice_areas():
    return render_template("practice_areas.html")


@app.route("/admin/inquiries")
def admin_inquiries():
    inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).all()
    return render_template("admin_inquiries.html", inquiries=inquiries)


if __name__ == "__main__":
    app.run(debug=True)