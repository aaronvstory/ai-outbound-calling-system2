"""
Main Flask application factory
"""
import os
from flask import Flask, jsonify
from flask_socketio import SocketIO

from ..config.settings import settings
from ..utils.logging import setup_logging, get_logger
from ..core.database import DatabaseService
from ..core.services import CallService
from .routes import register_routes
from .websocket import register_websocket_handlers
from .middleware import register_middleware

logger = get_logger(__name__)

def create_app(config_override=None):
    """Create and configure Flask application"""
    
    # Setup logging first
    setup_logging(
        log_level=settings.app.log_level,
        log_file="logs/app.log"
    )
    
    # Create Flask app
    app = Flask(__name__)
    
    # Configure app
    app.config['SECRET_KEY'] = settings.app.secret_key
    app.config['DEBUG'] = settings.app.debug
    
    # Override config if provided (for testing)
    if config_override:
        app.config.update(config_override)
    
    # Initialize SocketIO
    socketio = SocketIO(
        app, 
        cors_allowed_origins="*",
        async_mode='eventlet'
    )
    
    # Initialize services
    db_service = DatabaseService(settings.database.path)
    call_service = CallService(db_service)
    
    # Store services in app context
    app.db_service = db_service
    app.call_service = call_service
    app.socketio = socketio
    
    # Register components
    register_middleware(app)
    register_routes(app)
    register_websocket_handlers(socketio)
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint for monitoring"""
        try:
            # Test database connection
            db_service.get_calls(limit=1)
            
            return jsonify({
                'status': 'healthy',
                'version': '2.0.0',
                'database': 'connected',
                'synthflow': 'configured' if settings.synthflow.api_key else 'not_configured'
            }), 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return jsonify({
                'status': 'unhealthy',
                'error': str(e)
            }), 503
    
    logger.info("Flask application created successfully")
    return app

def run_app():
    """Run the application (for development)"""
    app = create_app()
    
    logger.info(f"Starting AI Calling System on {settings.app.host}:{settings.app.port}")
    logger.info(f"Debug mode: {settings.app.debug}")
    
    app.socketio.run(
        app,
        host=settings.app.host,
        port=settings.app.port,
        debug=settings.app.debug,
        allow_unsafe_werkzeug=True
    )

if __name__ == '__main__':
    run_app()