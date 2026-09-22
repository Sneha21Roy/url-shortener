"""
Helper utilities: short code generation, URL validation, QR code image
generation.
"""

import io
import random
import string

import qrcode
import validators


ALPHABET = string.ascii_letters + string.digits


def generate_short_code(length: int = 6) -> str:
    """Generate a random alphanumeric short code, e.g. 'aZ3kP9'."""
    return "".join(random.choices(ALPHABET, k=length))


def is_valid_url(url: str) -> bool:
    """Basic URL validation - must be a well-formed http(s) URL."""
    return bool(validators.url(url))


def generate_qr_code_bytes(data: str) -> bytes:
    """Generate a PNG QR code for the given data and return raw bytes."""
    img = qrcode.make(data)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()
