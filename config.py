"""
Application configuration, loaded from environment variables (.env).
"""

import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(os.getcwd(), "url_shortener.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Base URL used when building the short link shown to the user,
    # e.g. http://localhost:5000/abc123
    BASE_URL = os.environ.get("BASE_URL", "http://localhost:5000")

    SHORT_CODE_LENGTH = 6
