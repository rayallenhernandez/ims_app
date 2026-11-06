
import os
from datetime import timedelta
from urllib.parse import quote_plus

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "dev-secret-key-change-this"
    )

    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "3306")
    DB_NAME = os.environ.get("DB_NAME", "ims_db")

    database_url = os.environ.get("DATABASE_URL")
    mysql_url = os.environ.get("MYSQL_URL")

    if database_url:
        SQLALCHEMY_DATABASE_URI = database_url

    elif mysql_url:
        if mysql_url.startswith("mysql://"):
            mysql_url = "mysql+pymysql://" + mysql_url[len("mysql://"):]

        SQLALCHEMY_DATABASE_URI = mysql_url

    else:
        encoded_password = quote_plus(DB_PASSWORD)

        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://"
            f"{DB_USER}:{encoded_password}@"
            f"{DB_HOST}:{DB_PORT}/"
            f"{DB_NAME}"
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Database connection settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

    # Enable verified SSL when a CA certificate path is provided.
    DB_SSL_CA = os.environ.get("DB_SSL_CA")

    if DB_SSL_CA:
        SQLALCHEMY_ENGINE_OPTIONS["connect_args"] = {
            "ssl_verify_cert": True,
            "ssl_verify_identity": True,
            "ssl_ca": DB_SSL_CA,
        }

    UPLOAD_FOLDER = os.path.join(basedir, "uploads")

    ALLOWED_EXTENSIONS = {
        "pdf", "doc", "docx", "jpg", "jpeg", "png"
    }

    MAX_CONTENT_LENGTH = 10 * 1024 * 1024

    PERMANENT_SESSION_LIFETIME = timedelta(minutes=20)
    SESSION_REFRESH_EACH_REQUEST = True

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    REQUIRED_INTERNSHIP_HOURS = 240


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    PREFERRED_URL_SCHEME = "https"


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
