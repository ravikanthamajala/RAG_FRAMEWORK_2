"""
Flask application factory and initialization.

Automotive Market Analysis Platform
Project: China's Automotive Dominance - Strategic Analysis for Indian OEMs

Sets up the Flask app with configuration, CORS, MongoDB, blueprints for document uploads,
market analysis queries, forecasting, and policy recommendations.
"""

import logging

from flask import Flask, request
from flask_cors import CORS
from config import Config
from app.database import db

logger = logging.getLogger(__name__)


def _register_optional_blueprint(app, import_path, blueprint_name, url_prefix):
    """Register non-core blueprints without blocking app startup."""
    try:
        module = __import__(import_path, fromlist=[blueprint_name])
        blueprint = getattr(module, blueprint_name)
        app.register_blueprint(blueprint, url_prefix=url_prefix)
        logger.info("Registered optional blueprint %s at %s", import_path, url_prefix)
    except Exception as exc:
        logger.exception(
            "Skipping optional blueprint %s due to startup error: %s",
            import_path,
            exc,
        )


def create_app():
    """
    Create and configure the Flask application.

    Returns:
        Flask: The configured Flask app instance.
    """

    # Create Flask app instance
    app = Flask(__name__, static_folder='static', static_url_path='/static')

    # Load configuration from Config class
    app.config.from_object(Config)

    # Ensure MAX_CONTENT_LENGTH is set for file uploads
    app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH

    # Enable CORS for cross-origin requests with enhanced configuration
    # Support both localhost and 127.0.0.1 on port 3000 for frontend
    CORS(app,
         resources={r"/api/*": {
             "origins": [
                 "http://localhost:3000",
                 "http://127.0.0.1:3000",
                 "http://localhost:3001",  # Fallback port
                 "http://127.0.0.1:3001",
             ],
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
             "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
             "expose_headers": ["Content-Type", "X-Total-Count"],
             "supports_credentials": True,
             "max_age": 3600,
         }},
         send_wildcard=False,
         automatic_options=True,
         vary_header=True
    )

    # Add CORS headers middleware for debugging
    @app.after_request
    def add_cors_headers(response):
        """Add CORS headers to every response"""
        origin = request.headers.get('Origin')
        if origin in [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3001",
        ]:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response

    # Register core blueprints first so uploads/querying are not blocked by optional features.
    from app.routes.upload import upload_bp
    from app.routes.query import query_bp

    app.register_blueprint(upload_bp, url_prefix='/api')
    app.register_blueprint(query_bp, url_prefix='/api')

    optional_blueprints = [
        ('app.routes.analysis', 'analysis_bp', '/api'),
        ('app.routes.advanced', 'advanced_bp', '/api'),
        ('app.routes.forecast', 'forecast_bp', '/api'),
        ('app.routes.smart_upload', 'smart_upload_bp', '/api'),
        ('app.routes.test_charts', 'test_bp', '/api'),
        ('app.routes.forecast_insights', 'forecast_insights_bp', '/api'),
        ('app.routes.policy_simulation', 'policy_sim_bp', '/api'),
        ('app.routes.explanation_evaluation', 'explanation_evaluation_bp', '/api/explanation-evaluation'),
    ]
    for import_path, blueprint_name, url_prefix in optional_blueprints:
        _register_optional_blueprint(app, import_path, blueprint_name, url_prefix)

    @app.get('/api/health')
    def api_health():
        return {
            'status': 'ok',
            'service': 'agentic-rag-backend',
            'port': 4000,
        }, 200

    @app.errorhandler(413)
    def request_entity_too_large(_error):
        return {
            'error': 'Uploaded payload is too large',
            'message': (
                f"Maximum allowed request size is {Config.MAX_CONTENT_LENGTH // (1024 * 1024)} MB"
            ),
            'status': 'error',
        }, 413

    # Return the app
    return app