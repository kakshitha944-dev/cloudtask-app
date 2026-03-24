from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

# Shared SQLAlchemy instance — imported by app.py and bound to the Flask app.
db = SQLAlchemy()


class User(UserMixin, db.Model):
    """Represents an application user.

    Inherits UserMixin to satisfy Flask-Login's required interface
    (is_authenticated, is_active, get_id, etc.).
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    # Passwords are stored as bcrypt/werkzeug hashes — never plaintext.
    password = db.Column(db.String(200), nullable=False)

    # One-to-many relationship: a user owns many tasks.
    tasks = db.relationship("Task", backref="owner", lazy=True)

    def __repr__(self):
        return f"<User {self.username}>"


class Task(db.Model):
    """Represents a to-do task owned by a single user (CRUD entity)."""

    __tablename__ = "tasks"

    # Allowed status values — validated at the application layer in app.py.
    STATUS_PENDING = "pending"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_DONE = "done"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    # Default status is 'pending' when a task is first created.
    status = db.Column(db.String(20), nullable=False, default="pending")
    # Foreign key enforces referential integrity at the database level.
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )

    def __repr__(self):
        return f"<Task {self.id}: {self.title}>"
