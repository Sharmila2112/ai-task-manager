from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app import db
from app.models import Task

tasks_bp = Blueprint("tasks", __name__)


@tasks_bp.route("/")
@login_required
def index():
    """
    Show the current user's tasks, with optional search/filter via
    query string parameters, e.g. /?q=groceries&priority=High
    """
    query = Task.query.filter_by(user_id=current_user.id)

    search_term = request.args.get("q", "").strip()
    if search_term:
        query = query.filter(Task.title.ilike(f"%{search_term}%"))

    priority_filter = request.args.get("priority", "")
    if priority_filter in Task.PRIORITY_CHOICES:
        query = query.filter_by(priority=priority_filter)

    show_completed = request.args.get("show_completed", "all")
    if show_completed == "active":
        query = query.filter_by(is_completed=False)
    elif show_completed == "completed":
        query = query.filter_by(is_completed=True)

    tasks = query.order_by(Task.created_at.desc()).all()

    return render_template(
        "tasks.html",
        tasks=tasks,
        search_term=search_term,
        priority_filter=priority_filter,
        show_completed=show_completed,
        priorities=Task.PRIORITY_CHOICES,
    )


@tasks_bp.route("/tasks/new", methods=["GET", "POST"])
@login_required
def create_task():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "General").strip() or "General"
        priority = request.form.get("priority", "Medium")

        if not title:
            flash("Title is required.", "danger")
            return render_template(
                "task_form.html", priorities=Task.PRIORITY_CHOICES, task=None
            )

        if priority not in Task.PRIORITY_CHOICES:
            priority = "Medium"

        task = Task(
            title=title,
            description=description,
            category=category,
            priority=priority,
            user_id=current_user.id,
        )
        db.session.add(task)
        db.session.commit()

        flash("Task created.", "success")
        return redirect(url_for("tasks.index"))

    return render_template(
        "task_form.html", priorities=Task.PRIORITY_CHOICES, task=None
    )


@tasks_bp.route("/tasks/<int:task_id>/edit", methods=["GET", "POST"])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)

    # Ownership check: never trust that a URL parameter belongs to the
    # logged-in user. Without this, User A could edit User B's tasks
    # just by guessing task IDs in the URL.
    if task.user_id != current_user.id:
        flash("You do not have permission to edit that task.", "danger")
        return redirect(url_for("tasks.index"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            flash("Title is required.", "danger")
            return render_template(
                "task_form.html", priorities=Task.PRIORITY_CHOICES, task=task
            )

        task.title = title
        task.description = request.form.get("description", "").strip()
        task.category = request.form.get("category", "General").strip() or "General"

        priority = request.form.get("priority", "Medium")
        task.priority = priority if priority in Task.PRIORITY_CHOICES else "Medium"

        db.session.commit()
        flash("Task updated.", "success")
        return redirect(url_for("tasks.index"))

    return render_template(
        "task_form.html", priorities=Task.PRIORITY_CHOICES, task=task
    )


@tasks_bp.route("/tasks/<int:task_id>/toggle", methods=["POST"])
@login_required
def toggle_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash("You do not have permission to modify that task.", "danger")
        return redirect(url_for("tasks.index"))

    task.is_completed = not task.is_completed
    db.session.commit()
    return redirect(url_for("tasks.index"))


@tasks_bp.route("/tasks/<int:task_id>/delete", methods=["POST"])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash("You do not have permission to delete that task.", "danger")
        return redirect(url_for("tasks.index"))

    db.session.delete(task)
    db.session.commit()
    flash("Task deleted.", "info")
    return redirect(url_for("tasks.index"))
