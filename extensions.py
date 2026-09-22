"""
Shared Flask extension instances. Defined here (not in app.py) so
models.py and route modules can import them without circular imports.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
jwt = JWTManager()
