from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db


class User(UserMixin, db.Model):
    """
    A registered user.

    UserMixin (from Flask-Login) adds the properties/methods Flask-Login
    needs: is_authenticated, is_active, is_anonymous, get_id().
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # One-to-many: one user has many tasks.
    tasks = db.relationship(
        "Task", backref="owner", lazy=True, cascade="all, delete-orphan"
    )

    def set_password(self, password):
        """Hash and store the password. We NEVER store plaintext passwords."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Compare a plaintext password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"


class Task(db.Model):
    """A single task belonging to a user."""

    __tablename__ = "tasks"

    PRIORITY_CHOICES = ("Low", "Medium", "High")

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=True, default="General")
    priority = db.Column(db.String(10), nullable=False, default="Medium")
    is_completed = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Foreign key: links each task to exactly one user.
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    def __repr__(self):
        return f"<Task {self.title}>"
