import os
from datetime import timedelta
from urllib.parse import quote_plus


basedir = os.path.abspath(
    os.path.dirname(__file__)
)


class Config:
    """
    Base configuration for the City of Malabon University
    Internship Management System.
    """

    # =========================================================
    # SECRET KEY
    # =========================================================

    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "dev-secret-key-change-this"
    )


    # =========================================================
    # MYSQL DATABASE
    # =========================================================

    DB_USER = os.environ.get(
        "DB_USER",
        "root"
    )

    DB_PASSWORD = os.environ.get(
        "DB_PASSWORD",
        ""
    )

    DB_HOST = os.environ.get(
        "DB_HOST",
        "localhost"
    )

    DB_PORT = os.environ.get(
        "DB_PORT",
        "3306"
    )

    DB_NAME = os.environ.get(
        "DB_NAME",
        "ims_db"
    )


    # ---------------------------------------------------------
    # DATABASE URL
    # ---------------------------------------------------------
    #
    # Priority:
    # 1. DATABASE_URL
    # 2. MYSQL_URL
    # 3. Individual MySQL variables
    #
    # This allows the project to work locally and on
    # hosting platforms such as Railway.
    # ---------------------------------------------------------

    database_url = os.environ.get(
        "DATABASE_URL"
    )

    mysql_url = os.environ.get(
        "MYSQL_URL"
    )

    if database_url:

        SQLALCHEMY_DATABASE_URI = database_url

    elif mysql_url:

        # Railway may provide mysql://...
        # Explicitly use PyMySQL for SQLAlchemy.

        if mysql_url.startswith("mysql://"):

            mysql_url = (
                "mysql+pymysql://"
                + mysql_url[len("mysql://"):]
            )

        SQLALCHEMY_DATABASE_URI = mysql_url

    else:

        encoded_password = quote_plus(
            DB_PASSWORD
        )

        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://"
            f"{DB_USER}:{encoded_password}@"
            f"{DB_HOST}:{DB_PORT}/"
            f"{DB_NAME}"
        )


    SQLALCHEMY_TRACK_MODIFICATIONS = False


    # =========================================================
    # SQLALCHEMY ENGINE
    # =========================================================

    SQLALCHEMY_ENGINE_OPTIONS = {

        # Automatically test whether an existing
        # database connection is still usable.

        "pool_pre_ping": True,

        # Recycle connections periodically.

        "pool_recycle": 280,
    }


    # =========================================================
    # FILE UPLOADS
    # =========================================================

    UPLOAD_FOLDER = os.path.join(
        basedir,
        "uploads"
    )

    ALLOWED_EXTENSIONS = {
        "pdf",
        "doc",
        "docx",
        "jpg",
        "jpeg",
        "png",
    }

    MAX_CONTENT_LENGTH = (
        10 * 1024 * 1024
    )


    # =========================================================
    # SESSION / SECURITY
    # =========================================================

    PERMANENT_SESSION_LIFETIME = timedelta(
        minutes=20
    )

    SESSION_REFRESH_EACH_REQUEST = True

    SESSION_COOKIE_HTTPONLY = True

    SESSION_COOKIE_SAMESITE = "Lax"


    # =========================================================
    # OJT REQUIREMENTS
    # =========================================================

    REQUIRED_INTERNSHIP_HOURS = 240


# =============================================================
# DEVELOPMENT CONFIGURATION
# =============================================================

class DevelopmentConfig(Config):

    DEBUG = True

    # Local development uses HTTP,
    # so Secure cookies are disabled.

    SESSION_COOKIE_SECURE = False


# =============================================================
# PRODUCTION CONFIGURATION
# =============================================================

class ProductionConfig(Config):

    DEBUG = False

    # Production should use HTTPS.

    SESSION_COOKIE_SECURE = True

    # Flask-Login remember cookie, if used.

    REMEMBER_COOKIE_SECURE = True

    REMEMBER_COOKIE_HTTPONLY = True

    REMEMBER_COOKIE_SAMESITE = "Lax"

    # Tell Flask that HTTPS is the normal
    # external URL scheme.

    PREFERRED_URL_SCHEME = "https"


# =============================================================
# CONFIGURATION MAP
# =============================================================

config = {

    "development": DevelopmentConfig,

    "production": ProductionConfig,

    "default": DevelopmentConfig,

}