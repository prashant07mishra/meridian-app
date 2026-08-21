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

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "meridian_secret_key_2026")

# Database Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{BASE_DIR / 'meridian.db'}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Admin Credentials (configured via environment or defaults)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "meridian2026")

db.init_app(app)

with app.app_context():
  db.create_all()


@app.route("/", methods=["GET", "POST"])
def index():
  if request.method == "POST":
    name = request.form.get("name")
    email = request.form.get("email")
    message_body = request.form.get("message")

    new_inquiry = Inquiry(name=name, email=email, message=message_body)
    db.session.add(new_inquiry)
    db.session.commit()

    flash(
        f"Thank you, {name}. Your inquiry has been logged successfully!",
        "success",
    )
    return redirect(url_for("index") + "#contact")

  return render_template("index.html")


@app.route("/practice-areas")
def practice_areas():
  return render_template("practice_areas.html")


# --- Admin Authentication & Dashboard Routes ---


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
  if session.get("is_admin"):
    return redirect(url_for("admin_inquiries"))

  if request.method == "POST":
    username = request.form.get("username")
    password = request.form.get("password")

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
      session["is_admin"] = True
      flash("Logged in successfully.", "success")
      return redirect(url_for("admin_inquiries"))
    else:
      flash("Invalid admin credentials.", "danger")

  return render_template("admin_login.html")


@app.route("/admin/inquiries")
def admin_inquiries():
  if not session.get("is_admin"):
    flash("Please log in to access the admin portal.", "warning")
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