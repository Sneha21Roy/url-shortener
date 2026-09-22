"""
Database models.

Schema overview:
    User (1) ----< (many) URL (1) ----< (many) Click

- A URL can optionally belong to a User (anonymous short links are allowed,
  just like most public URL shorteners).
- Every redirect hit is logged as a Click row, which is what powers the
  analytics dashboard (total clicks, clicks over time, referrers, etc.)
  without needing to store a running counter that could get out of sync.
"""

from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db


def utcnow():
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    urls = db.relationship("URL", backref="owner", lazy="dynamic", cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat(),
        }


class URL(db.Model):
    __tablename__ = "urls"

    id = db.Column(db.Integer, primary_key=True)
    short_code = db.Column(db.String(32), unique=True, nullable=False, index=True)
    original_url = db.Column(db.Text, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    clicks = db.relationship("Click", backref="url", lazy="dynamic", cascade="all, delete-orphan")

    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return utcnow() > self.expires_at

    def to_dict(self, base_url: str = "") -> dict:
        return {
            "id": self.id,
            "short_code": self.short_code,
            "short_url": f"{base_url}/{self.short_code}" if base_url else self.short_code,
            "original_url": self.original_url,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_active": self.is_active,
            "total_clicks": self.clicks.count(),
        }


class Click(db.Model):
    __tablename__ = "clicks"

    id = db.Column(db.Integer, primary_key=True)
    url_id = db.Column(db.Integer, db.ForeignKey("urls.id"), nullable=False, index=True)
    clicked_at = db.Column(db.DateTime, default=utcnow, index=True)
    ip_address = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    referrer = db.Column(db.String(255), nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "clicked_at": self.clicked_at.isoformat(),
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "referrer": self.referrer,
        }
