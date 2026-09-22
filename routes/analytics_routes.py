"""
Analytics + QR code API.

    GET /api/analytics/<short_code>  -> click stats for one short URL
                                         (public for anonymous links, owner-only
                                         for links created while logged in)
    GET /api/qr/<short_code>         -> PNG QR code image for the short link
"""

from collections import Counter
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, current_app, Response
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request

from models import URL
from utils import generate_qr_code_bytes

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api")


def _get_authorized_url_or_none(short_code):
    """
    Returns the URL object if it exists and the current caller is allowed
    to view its analytics (anyone for anonymous links, owner-only otherwise).
    Returns (url_obj, error_response_or_None).
    """
    url_obj = URL.query.filter_by(short_code=short_code).first()
    if not url_obj:
        return None, (jsonify({"error": "short URL not found"}), 404)

    if url_obj.owner_id is not None:
        # Owned link - require a matching JWT
        try:
            verify_jwt_in_request(optional=True)
        except Exception:
            pass
        user_id = get_jwt_identity()
        if not user_id or int(user_id) != url_obj.owner_id:
            return None, (jsonify({"error": "you do not have access to this URL's analytics"}), 403)

    return url_obj, None


@analytics_bp.route("/analytics/<short_code>", methods=["GET"])
def analytics(short_code):
    url_obj, error = _get_authorized_url_or_none(short_code)
    if error:
        return error

    clicks = url_obj.clicks.order_by("clicked_at").all()
    total_clicks = len(clicks)

    # Clicks per day, for the last 14 days (great for a simple line chart)
    now = datetime.now(timezone.utc)
    days = [(now - timedelta(days=i)).date() for i in range(13, -1, -1)]
    clicks_by_day = Counter(c.clicked_at.date() for c in clicks)
    daily_series = [
        {"date": d.isoformat(), "clicks": clicks_by_day.get(d, 0)} for d in days
    ]

    referrer_counts = Counter((c.referrer or "Direct / unknown") for c in clicks)
    top_referrers = [
        {"referrer": ref, "count": count}
        for ref, count in referrer_counts.most_common(10)
    ]

    return jsonify(
        {
            "short_code": url_obj.short_code,
            "original_url": url_obj.original_url,
            "created_at": url_obj.created_at.isoformat(),
            "total_clicks": total_clicks,
            "daily_clicks": daily_series,
            "top_referrers": top_referrers,
        }
    ), 200


@analytics_bp.route("/qr/<short_code>", methods=["GET"])
def qr_code(short_code):
    url_obj = URL.query.filter_by(short_code=short_code).first()
    if not url_obj:
        return jsonify({"error": "short URL not found"}), 404

    short_url = f"{current_app.config['BASE_URL']}/{url_obj.short_code}"
    png_bytes = generate_qr_code_bytes(short_url)
    return Response(png_bytes, mimetype="image/png")
