"""
Health Check Route for Backend Server Monitoring

Provides endpoints to verify backend server status and connectivity.
Used by frontend to detect if backend is running and accessible.
"""

from flask import Blueprint, jsonify, request
import logging

# Create health check blueprint
health_bp = Blueprint('health', __name__)
logger = logging.getLogger(__name__)


@health_bp.route('/health', methods=['GET', 'OPTIONS'])
def health_check():
    """
    Health check endpoint.
    
    Returns:
        JSON response with server status
    """
    if request.method == 'OPTIONS':
        return '', 204
    
    return jsonify({
        'status': 'ok',
        'message': 'Backend server is running',
        'service': 'Agentic RAG Document Assistant',
    }), 200


@health_bp.route('/health/detailed', methods=['GET', 'OPTIONS'])
def detailed_health():
    """
    Detailed health check with more information.
    
    Returns:
        JSON response with detailed server and database status
    """
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        from app.database import db
        
        # Basic connection test
        db_status = 'connected'
        try:
            # This will attempt a basic DB operation
            db.posts.count_documents({}) if hasattr(db, 'posts') else 0
        except Exception as e:
            db_status = f'error: {str(e)}'
        
        return jsonify({
            'status': 'ok',
            'message': 'Backend server is operational',
            'service': 'Agentic RAG Document Assistant',
            'database': db_status,
            'version': '1.0.0',
        }), 200
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'status': 'degraded',
            'message': f'Server running but database check failed: {str(e)}',
            'service': 'Agentic RAG Document Assistant',
        }), 200


# Handle CORS preflight
@health_bp.before_request
def handle_preflight():
    from flask import request
    if request.method == 'OPTIONS':
        return '', 204
