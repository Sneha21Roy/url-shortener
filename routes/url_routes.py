"""
Core URL shortening API.

    POST /api/shorten        {original_url, custom_alias?} -> creates a short URL
                              (Authorization header optional - if a valid JWT
                              is provided, the URL is linked to that user)
    GET  /api/urls            (JWT required) -> list the current user's URLs
    DELETE /api/urls/<code>   (JWT required) -> delete one of the user's URLs
    GET  /<short_code>        -> redirects to the original URL and logs a Click
"""

from datetime import datetime, timezone

from flask import Blueprint, request, jsonify, redirect, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models import URL, Click
from utils import generate_short_code, is_valid_url

url_bp = Blueprint("url", __name__)


@url_bp.route("/api/shorten", methods=["POST"])
@jwt_required(optional=True)
def shorten():
    data = request.get_json(silent=True) or {}
    original_url = (data.get("original_url") or "").strip()
    custom_alias = (data.get("custom_alias") or "").strip() or None
    expires_at_raw = data.get("expires_at")  # optional ISO datetime string

    if not original_url:
        return jsonify({"error": "original_url is required"}), 400
    if not is_valid_url(original_url):
        return jsonify({"error": "original_url is not a valid http(s) URL"}), 400

    if custom_alias:
        if not custom_alias.isalnum():
            return jsonify({"error": "custom_alias must be alphanumeric"}), 400
        if URL.query.filter_by(short_code=custom_alias).first():
            return jsonify({"error": "this custom alias is already taken"}), 409
        short_code = custom_alias
    else:
        short_code = generate_short_code(current_app.config["SHORT_CODE_LENGTH"])
        # Extremely unlikely, but guard against collisions
        while URL.query.filter_by(short_code=short_code).first():
            short_code = generate_short_code(current_app.config["SHORT_CODE_LENGTH"])

    expires_at = None
    if expires_at_raw:
        try:
            expires_at = datetime.fromisoformat(expires_at_raw)
        except ValueError:
            return jsonify({"error": "expires_at must be a valid ISO datetime string"}), 400

    user_id = get_jwt_identity()  # None if request wasn't authenticated

    url_obj = URL(
        short_code=short_code,
        original_url=original_url,
        owner_id=int(user_id) if user_id else None,
        expires_at=expires_at,
    )
    db.session.add(url_obj)
    db.session.commit()

    return jsonify(url_obj.to_dict(base_url=current_app.config["BASE_URL"])), 201


@url_bp.route("/api/urls", methods=["GET"])
@jwt_required()
def list_urls():
    user_id = int(get_jwt_identity())
    urls = URL.query.filter_by(owner_id=user_id).order_by(URL.created_at.desc()).all()
    return jsonify(
        {"urls": [u.to_dict(base_url=current_app.config["BASE_URL"]) for u in urls]}
    ), 200


@url_bp.route("/api/urls/<short_code>", methods=["DELETE"])
@jwt_required()
def delete_url(short_code):
    user_id = int(get_jwt_identity())
    url_obj = URL.query.filter_by(short_code=short_code, owner_id=user_id).first()
    if not url_obj:
        return jsonify({"error": "URL not found or you don't have permission to delete it"}), 404
    db.session.delete(url_obj)
    db.session.commit()
    return jsonify({"message": "deleted"}), 200


@url_bp.route("/<short_code>", methods=["GET"])
def redirect_to_original(short_code):
    url_obj = URL.query.filter_by(short_code=short_code).first()
    if not url_obj or not url_obj.is_active:
        return jsonify({"error": "short URL not found"}), 404
    if url_obj.is_expired():
        return jsonify({"error": "this short URL has expired"}), 410

    click = Click(
        url_id=url_obj.id,
        ip_address=request.remote_addr,
        user_agent=request.headers.get("User-Agent", "")[:255],
        referrer=request.referrer,
    )
    db.session.add(click)
    db.session.commit()

    return redirect(url_obj.original_url, code=302)
