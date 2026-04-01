import os
import re
from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, User, Task
from flask_login import (
    LoginManager,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash

# ── Application factory ────────────────────────────────────────────────────
app = Flask(__name__)

# SECRET_KEY must always come from an environment variable in production.
# A hardcoded fallback is acceptable only for local development.
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", os.urandom(24))

# DATABASE_URL env var lets us swap to PostgreSQL on EC2 without code changes.
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///tasks.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

with app.app_context():
    db.create_all()


# ── User loader (required by Flask-Login) ──────────────────────────────────
@login_manager.user_loader
def load_user(user_id):
    """Load a user from the database by primary key."""
    return User.query.get(int(user_id))


# ── Helper: simple e-mail format validation ────────────────────────────────
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(email):
    """Return True if *email* passes a basic format check."""
    return bool(EMAIL_REGEX.match(email))


# ── REGISTER ───────────────────────────────────────────────────────────────
@app.route("/register", methods=["GET", "POST"])
def register():
    """Handle new-user registration with server-side input validation."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        # Validate: all fields present
        if not username or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for("register"))

        # Validate: email format
        if not is_valid_email(email):
            flash("Please enter a valid email address.", "danger")
            return redirect(url_for("register"))

        # Validate: minimum password length
        if len(password) < 8:
            flash("Password must be at least 8 characters.", "danger")
            return redirect(url_for("register"))

        # Validate: username length
        if len(username) > 80:
            flash("Username must be 80 characters or fewer.", "danger")
            return redirect(url_for("register"))

        # Validate: duplicate email
        if User.query.filter_by(email=email).first():
            flash("That email is already registered.", "danger")
            return redirect(url_for("register"))

        # Validate: duplicate username
        if User.query.filter_by(username=username).first():
            flash("That username is already taken.", "danger")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)
        new_user = User(
            username=username,
            email=email,
            password=hashed_password,
        )
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful — please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


# ── LOGIN ──────────────────────────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    """Authenticate an existing user."""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash("Email and password are required.", "danger")
            return redirect(url_for("login"))

        user = User.query.filter_by(email=email).first()

        # Deliberately vague message to prevent user enumeration
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("index"))

        flash("Invalid email or password.", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")


# ── LOGOUT ─────────────────────────────────────────────────────────────────
@app.route("/logout")
@login_required
def logout():
    """Log the current user out and redirect to login."""
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# ── HOME / TASK LIST ───────────────────────────────────────────────────────
@app.route("/")
@login_required
def index():
    """Display all tasks belonging to the logged-in user."""
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    return render_template("index.html", tasks=tasks)


# ── ADD TASK ───────────────────────────────────────────────────────────────
@app.route("/add", methods=["GET", "POST"])
@login_required
def add_task():
    """Create a new task for the current user."""
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()

        if not title:
            flash("Task title cannot be empty.", "danger")
            return redirect(url_for("add_task"))

        if len(title) > 120:
            flash("Title must be 120 characters or fewer.", "danger")
            return redirect(url_for("add_task"))

        new_task = Task(
            title=title,
            description=description,
            user_id=current_user.id,
        )
        db.session.add(new_task)
        db.session.commit()

        flash("Task added successfully.", "success")
        return redirect(url_for("index"))

    return render_template("add_task.html")


# ── EDIT TASK ──────────────────────────────────────────────────────────────
@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
@login_required
def edit_task(task_id):
    """Edit an existing task — only the owner may edit."""
    task = Task.query.get_or_404(task_id)

    # Ownership check: prevent horizontal privilege escalation
    if task.user_id != current_user.id:
        flash("You are not authorised to edit this task.", "danger")
        return redirect(url_for("index"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        status = request.form.get("status", "pending").strip()

        if not title:
            flash("Task title cannot be empty.", "danger")
            return redirect(url_for("edit_task", task_id=task_id))

        if len(title) > 120:
            flash("Title must be 120 characters or fewer.", "danger")
            return redirect(url_for("edit_task", task_id=task_id))

        allowed_statuses = {"pending", "in_progress", "done"}
        if status not in allowed_statuses:
            flash("Invalid status value.", "danger")
            return redirect(url_for("edit_task", task_id=task_id))

        task.title = title
        task.description = description
        task.status = status
        db.session.commit()

        flash("Task updated.", "success")
        return redirect(url_for("index"))

    return render_template("edit_task.html", task=task)


# ── DELETE TASK ────────────────────────────────────────────────────────────
@app.route("/delete/<int:task_id>", methods=["POST"])
@login_required
def delete_task(task_id):
    """Delete a task — only the owner may delete. Uses POST to prevent CSRF."""
    task = Task.query.get_or_404(task_id)

    # Ownership check: prevent horizontal privilege escalation
    if task.user_id != current_user.id:
        flash("You are not authorised to delete this task.", "danger")
        return redirect(url_for("index"))

    db.session.delete(task)
    db.session.commit()

    flash("Task deleted.", "success")
    return redirect(url_for("index"))


# ── Entry point ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # debug=False is mandatory — debug mode exposes an interactive console
    app.run(host="0.0.0.0", port=5000, debug=False)
