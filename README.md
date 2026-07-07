# Task Manager

A full-stack Python task management app with user authentication, task CRUD,
search, priorities, and categories.

**Stack:** Flask, SQLAlchemy, Flask-Migrate, Flask-Login, SQLite (dev) /
PostgreSQL (prod), Bootstrap 5.

---

## Project Structure

```
task-manager/
├── app/
│   ├── __init__.py          # Application factory
│   ├── models.py            # User and Task database models
│   ├── routes/
│   │   ├── auth.py          # Register / login / logout
│   │   └── tasks.py         # Task CRUD + search
│   ├── templates/           # Jinja2 HTML templates
│   └── static/
│       └── style.css
├── migrations/               # Flask-Migrate / Alembic migration history
├── instance/                 # SQLite DB lives here (gitignored)
├── config.py                 # Dev / Prod / Testing configs
├── run.py                    # Entry point
├── requirements.txt
├── Procfile                  # For Render/Railway deployment
└── .env.example
```

---

## Local Setup

```bash
# 1. Clone / unzip the project, then cd into it
cd task-manager

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy env file and edit SECRET_KEY
cp .env.example .env

# 5. Set environment variables (or use python-dotenv / export manually)
export FLASK_APP=run.py
export FLASK_ENV=development

# 6. Apply database migrations (creates instance/app.db)
flask db upgrade

# 7. Run the app
python run.py
```

Visit **http://127.0.0.1:5000**, register an account, and start creating tasks.

---

## Database Migrations

Whenever you change `app/models.py`:

```bash
flask db migrate -m "Describe your change"
flask db upgrade
```

`flask db migrate` generates a new migration script by diffing your models
against the current DB schema. `flask db upgrade` actually applies it.

---

## Deployment (Render / Railway)

1. Push this project to a GitHub repo.
2. Create a new Web Service on Render or Railway, connect the repo.
3. Add a PostgreSQL database add-on — this sets a `DATABASE_URL` env var automatically.
4. Set environment variables in the dashboard:
   - `FLASK_ENV=production`
   - `SECRET_KEY=<a long random string>`
5. Build command: `pip install -r requirements.txt`
6. Start command (from `Procfile`): `gunicorn run:app`
   The `release: flask db upgrade` line in the Procfile runs migrations
   automatically on each deploy (Render/Railway both support release phases;
   check your platform's docs if it's not picked up automatically).

---

## Features Implemented

- [x] User registration with password confirmation
- [x] Secure password hashing (Werkzeug `generate_password_hash`)
- [x] Login / logout via Flask-Login sessions
- [x] Task CRUD (create, read, update, delete)
- [x] Task priority (Low / Medium / High)
- [x] Task categories (free text)
- [x] Search by title
- [x] Filter by priority and completion status
- [x] Per-user data isolation (users can only see/edit their own tasks)
- [x] Responsive Bootstrap UI
- [x] SQLite for dev, PostgreSQL for production (via `config.py`)
- [x] Flask-Migrate for schema versioning

## Not Yet Implemented (future work)

- Password reset / "forgot password" flow
- Email verification
- Due dates and reminders
- Pagination for large task lists
- REST API endpoints (JSON) for a future frontend framework (React/Vue) or mobile app
- AI features (explicitly deferred per project scope)
