import os
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

# Email / SMTP Configuration (SSL over Port 465)
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = ("Meridian Inquiries", os.getenv("MAIL_USERNAME"))

# Initialize Extensions
db.init_app(app)
mail = Mail(app)

with app.app_context():
    db.create_all()


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message_body = request.form.get("message")

        # 1. Save to SQLite database
        new_inquiry = Inquiry(name=name, email=email, message=message_body)
        db.session.add(new_inquiry)
        db.session.commit()

        # 2. Check credentials dynamically
        mail_user = os.getenv("MAIL_USERNAME")
        mail_pass = os.getenv("MAIL_PASSWORD")
        recipient_target = os.getenv("MAIL_RECEIVER") or mail_user

        if not recipient_target or not mail_pass:
            print("WARNING: Email credentials missing in environment variables. Inquiry saved locally.")
            flash(f"Thank you, {name}. Your inquiry has been received!", "info")
            return redirect(url_for("index") + "#contact")

        # 3. Send email with error handling
        try:
            msg = Message(
                subject=f"New Advisory Inquiry from {name}",
                recipients=[recipient_target],
                body=f"Name: {name}\nEmail: {email}\n\nMessage:\n{message_body}",
            )
            mail.send(msg)
            flash(f"Thank you, {name}. Your inquiry has been sent successfully!", "success")
        except Exception as e:
            print(f"Email dispatch error: {e}")
            flash(f"Thank you, {name}. Your inquiry was received and logged.", "info")

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