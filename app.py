"""
Flask application factory.

Run with:  python app.py   (dev server)
       or: flask --app app run
"""

from flask import Flask, render_template, jsonify
from dotenv import load_dotenv

from config import Config
from extensions import db, jwt

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)

    # Register blueprints
    from routes.auth_routes import auth_bp
    from routes.url_routes import url_bp
    from routes.analytics_routes import analytics_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(url_bp)
    app.register_blueprint(analytics_bp)

    with app.app_context():
        db.create_all()

    @app.route("/")
    def dashboard():
        return render_template("dashboard.html", base_url=app.config["BASE_URL"])

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "not found"}), 404

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
