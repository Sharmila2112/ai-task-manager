import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

from config import config

# Extensions are created here but not bound to an app yet.
# This lets us use the "application factory" pattern below.
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


def create_app(config_name=None):
    """
    Application factory.

    Instead of creating a single global `app` object, we build it inside
    a function. This makes it possible to create multiple app instances
    with different configs (e.g. one for tests, one for production)
    without them interfering with each other.
    """
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config[config_name])

    # Make sure the instance folder exists (holds the SQLite file, secrets, etc.)
    os.makedirs(app.instance_path, exist_ok=True)

    # Bind extensions to this specific app instance.
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Where Flask-Login redirects unauthenticated users.
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"

    # Import models here (not at top of file) to avoid circular imports:
    # models.py imports `db` from this file, so this file must finish
    # defining `db` before models.py is imported.
    from app import models

    @login_manager.user_loader
    def load_user(user_id):
        """Flask-Login calls this on every request to reload the user
        object from the ID stored in the session cookie."""
        return models.User.query.get(int(user_id))

    # Register blueprints (modular route groups).
    from app.routes.auth import auth_bp
    from app.routes.tasks import tasks_bp
    from app.routes.ai import ai_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(ai_bp)

    return app
