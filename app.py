import os
from pathlib import Path
from dotenv import load_dotenv
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from models import Inquiry, db

# Explicitly load .env from the exact directory of app.py
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback_dev_secret_key_2026")

# Database Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{BASE_DIR / 'meridian.db'}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize Extensions
db.init_app(app)

with app.app_context():
  db.create_all()


# --- Public Client Routes ---


@app.route("/", methods=["GET", "POST"])
def index():
  if request.method == "POST":
    name = request.form.get("name")
    email = request.form.get("email")
    message_body = request.form.get("message")

    # Save inquiry to SQLite database
    new_inquiry = Inquiry(name=name, email=email, message=message_body)
    db.session.add(new_inquiry)
    db.session.commit()

    flash(
        f"Thank you, {name}. Your inquiry has been received and recorded!",
        "success",
    )
    return redirect(url_for("index") + "#contact")

  return render_template("index.html")


@app.route("/practice-areas")
def practice_areas():
  return render_template("practice_areas.html")


# --- Admin Portal Routes ---


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
  if session.get("is_admin"):
    return redirect(url_for("admin_inquiries"))

  if request.method == "POST":
    username = request.form.get("username")
    password = request.form.get("password")

    admin_username = os.getenv("ADMIN_USERNAME")
    admin_password = os.getenv("ADMIN_PASSWORD")

    # Strict check requiring both environment variables to be set
    if (
        admin_username
        and admin_password
        and username == admin_username
        and password == admin_password
    ):
      session["is_admin"] = True
      flash("Logged in successfully.", "success")
      return redirect(url_for("admin_inquiries"))
    else:
      flash("Invalid admin username or password.", "danger")

  return render_template("admin_login.html")


@app.route("/admin/inquiries")
def admin_inquiries():
  if not session.get("is_admin"):
    flash("Please log in to access the inquiry database.", "warning")
    return redirect(url_for("admin_login"))

  inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).all()
  return render_template("admin_inquiries.html", inquiries=inquiries)


@app.route("/admin/logout")
def admin_logout():
  session.pop("is_admin", None)
  flash("Logged out successfully.", "info")
  return redirect(url_for("admin_login"))


if __name__ == "__main__":
  app.run(debug=True)