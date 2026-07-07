import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration shared by all environments."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

class DevelopmentConfig(Config):
    """Local development: SQLite, debug on."""

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'instance', 'app.db')}"
    )


class ProductionConfig(Config):
    """Production: PostgreSQL, debug off."""

    DEBUG = False
    # Render/Railway provide DATABASE_URL starting with 'postgres://';
    # SQLAlchemy 1.4+/2.x requires 'postgresql://'.
    uri = os.environ.get("DATABASE_URL", "")
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = uri


class TestingConfig(Config):
    """Used for automated tests: in-memory database."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
