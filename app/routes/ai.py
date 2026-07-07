import json
from flask import Blueprint, render_template, request, current_app
from flask_login import login_required, current_user
from google import genai
from google.genai import types

from app.models import Task, db

ai_bp = Blueprint("ai", __name__, url_prefix="/ai")

# Gemini model used for both features. See Google's model list for current
# options: https://ai.google.dev/gemini-api/docs/models
MODEL_NAME = "gemini-2.5-flash"


def _get_client():
    """
    Build a Gemini API client using the key from app config.
    Returns None if no key is configured, so callers can show a
    friendly error instead of crashing.
    """
    api_key = current_app.config.get("GEMINI_API_KEY")
    if not api_key:
        return None
    return genai.Client(api_key=api_key)


def _task_summary_for_user(user_id):
    """Build a compact text summary of a user's tasks to give Gemini context."""
    tasks = Task.query.filter_by(user_id=user_id).order_by(Task.created_at.desc()).all()
    if not tasks:
        return "The user currently has no tasks."

    lines = []
    for t in tasks:
        status = "completed" if t.is_completed else "pending"
        lines.append(f"- [{status}] \"{t.title}\" (priority: {t.priority}, category: {t.category})")
    return "\n".join(lines)


@ai_bp.route("/assistant", methods=["GET", "POST"])
@login_required
def assistant():
    """
    Chat-style assistant. The user types a natural-language message.
    Gemini is asked to respond with structured JSON (using the API's
    native JSON mode) so we can reliably decide whether to create a
    task or just reply conversationally.
    """
    reply_text = None
    error = None

    if request.method == "POST":
        user_message = request.form.get("message", "").strip()

        if not user_message:
            error = "Please type a message."
        else:
            client = _get_client()
            if client is None:
                error = (
                    "No GEMINI_API_KEY is configured. Add one to your .env file "
                    "to enable the AI assistant."
                )
            else:
                task_context = _task_summary_for_user(current_user.id)

                system_prompt = (
                    "You are a task-management assistant embedded in a to-do app. "
                    "You will be given the user's current task list and a message from them. "
                    "Decide whether the user is asking you to add/create a task, or just "
                    "chatting/asking a question. "
                    "Use action='create_task' only when the user clearly asked to add/create "
                    "a task; otherwise use action='none' and leave title/category/priority as "
                    "empty strings. "
                    "'reply' should be a short, friendly, plain-language response to show the "
                    "user, referencing their actual tasks below when relevant.\n\n"
                    f"Current tasks:\n{task_context}"
                )

                response_schema = {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["create_task", "none"]},
                        "title": {"type": "string"},
                        "category": {"type": "string"},
                        "priority": {"type": "string", "enum": ["Low", "Medium", "High"]},
                        "reply": {"type": "string"},
                    },
                    "required": ["action", "title", "category", "priority", "reply"],
                }

                try:
                    response = client.models.generate_content(
                        model=MODEL_NAME,
                        contents=user_message,
                        config=types.GenerateContentConfig(
                            system_instruction=system_prompt,
                            response_mime_type="application/json",
                            response_schema=response_schema,
                            max_output_tokens=500,
                        ),
                    )
                    parsed = json.loads(response.text)

                    if parsed.get("action") == "create_task" and parsed.get("title"):
                        priority = parsed.get("priority", "Medium")
                        if priority not in Task.PRIORITY_CHOICES:
                            priority = "Medium"

                        new_task = Task(
                            title=parsed["title"],
                            category=parsed.get("category") or "General",
                            priority=priority,
                            user_id=current_user.id,
                        )
                        db.session.add(new_task)
                        db.session.commit()

                    reply_text = parsed.get("reply", "Done.")

                except json.JSONDecodeError:
                    reply_text = response.text
                except Exception as exc:
                    error = f"AI assistant error: {exc}"

    return render_template("ai_assistant.html", reply_text=reply_text, error=error)


@ai_bp.route("/report")
@login_required
def progress_report():
    """
    Computes real stats from the user's tasks, then asks Gemini to turn
    those stats into a short, readable progress summary with suggestions.
    """
    tasks = Task.query.filter_by(user_id=current_user.id).all()

    total = len(tasks)
    completed = sum(1 for t in tasks if t.is_completed)
    pending = total - completed

    by_priority = {"High": 0, "Medium": 0, "Low": 0}
    for t in tasks:
        by_priority[t.priority] = by_priority.get(t.priority, 0) + 1

    by_category = {}
    for t in tasks:
        by_category[t.category] = by_category.get(t.category, 0) + 1

    stats = {
        "total": total,
        "completed": completed,
        "pending": pending,
        "completion_rate": round((completed / total) * 100, 1) if total else 0,
        "by_priority": by_priority,
        "by_category": by_category,
    }

    ai_summary = None
    error = None

    client = _get_client()
    if client is None:
        error = "No GEMINI_API_KEY is configured. Add one to your .env file to enable AI summaries."
    elif total == 0:
        ai_summary = "You have no tasks yet, so there's nothing to report on. Add a few tasks to get started!"
    else:
        prompt = (
            "Here are a user's task statistics from a to-do app:\n"
            f"{json.dumps(stats, indent=2)}\n\n"
            "Write a short (4-6 sentence), encouraging progress report in plain English. "
            "Mention their completion rate, call out anything notable (e.g. many high-priority "
            "tasks still pending), and give one concrete, actionable suggestion for what to focus "
            "on next. Do not repeat the raw numbers as a list; write it as flowing prose."
        )
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(max_output_tokens=400),
            )
            ai_summary = response.text.strip()
        except Exception as exc:
            error = f"AI report error: {exc}"

    return render_template(
        "progress_report.html", stats=stats, ai_summary=ai_summary, error=error
    )