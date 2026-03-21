import os
from flask import Flask, render_template, request, redirect, url_for
from models import db, User, Task
from flask_login import (
    LoginManager,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key')
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tasks.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        if not username or not email or not password:
            return "All fields are required"

        hashed_password = generate_password_hash(password)

        new_user = User(
            username=username,
            email=email,
            password=hashed_password,
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.html")


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(
            user.password,
            password,
        ):
            login_user(user)
            return redirect(url_for("index"))

        return "Invalid credentials"

    return render_template("login.html")


# ---------------- LOGOUT ----------------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# ---------------- HOME ----------------
@app.route("/")
@login_required
def index():
    tasks = Task.query.filter_by(
        user_id=current_user.id
    ).all()

    return render_template(
        "index.html",
        tasks=tasks,
    )


# ---------------- ADD TASK ----------------
@app.route("/add", methods=["GET", "POST"])
@login_required
def add_task():
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]

        if not title.strip():
            return "Title cannot be empty"

        new_task = Task(
            title=title,
            description=description,
            user_id=current_user.id,
        )

        db.session.add(new_task)
        db.session.commit()

        return redirect(url_for("index"))

    return render_template("add_task.html")


# ---------------- DELETE TASK ----------------
@app.route("/delete/<int:id>")
@login_required
def delete_task(id):
    task = Task.query.get_or_404(id)

    if task.user_id != current_user.id:
        return "Unauthorized"

    db.session.delete(task)
    db.session.commit()

    return redirect(url_for("index"))


# ---------------- EDIT TASK ----------------
@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_task(id):
    task = Task.query.get_or_404(id)

    if task.user_id != current_user.id:
        return "Unauthorized"

    if request.method == "POST":
        task.title = request.form["title"]
        task.description = request.form["description"]
        task.status = request.form["status"]

        db.session.commit()
        return redirect(url_for("index"))

    return render_template(
        "edit_task.html",
        task=task,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
