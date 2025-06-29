"""
Flask routes for the web application
"""
from flask import request, jsonify, render_template
import uuid
from datetime import datetime

from ..core.models import CallRequest, Call
from ..utils.logging import get_logger
from ..utils.validators import validate_call_request

logger = get_logger(__name__)

def register_routes(app):
    """Register all Flask routes"""
    
    @app.route('/')
    def index():
        """Main dashboard page"""
        return render_template('index.html')
    
    @app.route('/api/calls', methods=['POST'])
    def create_call():
        """Create a new outbound call"""
        try:
            data = request.get_json()
            
            # Validate request data
            validation_errors = validate_call_request(data)
            if validation_errors:
                return jsonify({
                    'success': False,
                    'error': 'Validation failed',
                    'details': validation_errors
                }), 400
            
            # Create call request
            call_request = CallRequest(
                caller_name=data['caller_name'],
                caller_phone=data['caller_phone'],
                phone_number=data['phone_number'],
                account_action=data['account_action'],
                additional_info=data.get('additional_info', '')
            )
            
            # Create call
            call = Call(
                id=str(uuid.uuid4()),
                request=call_request
            )
            
            # Initiate call through service
            success = app.call_service.initiate_call(call)
            
            if success:
                return jsonify({
                    'success': True,
                    'call_id': call.id,
                    'message': 'Call initiated successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to initiate call'
                }), 500
                
        except Exception as e:
            logger.error(f"Error creating call: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/calls', methods=['GET'])
    def get_calls():
        """Get all calls with pagination"""
        try:
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 50))
            status_filter = request.args.get('status')
            
            offset = (page - 1) * per_page
            
            # Get calls from service
            calls = app.call_service.get_calls(
                limit=per_page,
                offset=offset,
                status_filter=status_filter
            )
            
            # Convert to dict for JSON response
            calls_data = []
            for call in calls:
                calls_data.append({
                    'id': call.id,
                    'caller_name': call.request.caller_name,
                    'caller_phone': call.request.caller_phone,
                    'phone_number': call.request.phone_number,
                    'account_action': call.request.account_action,
                    'additional_info': call.request.additional_info,
                    'status': call.status.value,
                    'created_at': call.created_at.isoformat(),
                    'completed_at': call.completed_at.isoformat() if call.completed_at else None,
                    'duration': call.duration,
                    'success': call.success,
                    'transcript': call.transcript,
                    'error_message': call.error_message
                })
            
            return jsonify({
                'success': True,
                'calls': calls_data,
                'page': page,
                'per_page': per_page
            })
            
        except Exception as e:
            logger.error(f"Error getting calls: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/calls/<call_id>', methods=['GET'])
    def get_call(call_id):
        """Get specific call details"""
        try:
            call = app.call_service.get_call(call_id)
            
            if not call:
                return jsonify({
                    'success': False,
                    'error': 'Call not found'
                }), 404
            
            call_data = {
                'id': call.id,
                'caller_name': call.request.caller_name,
                'caller_phone': call.request.caller_phone,
                'phone_number': call.request.phone_number,
                'account_action': call.request.account_action,
                'additional_info': call.request.additional_info,
                'status': call.status.value,
                'created_at': call.created_at.isoformat(),
                'completed_at': call.completed_at.isoformat() if call.completed_at else None,
                'duration': call.duration,
                'success': call.success,
                'transcript': call.transcript,
                'error_message': call.error_message,
                'metadata': call.metadata
            }
            
            return jsonify({
                'success': True,
                'call': call_data
            })
            
        except Exception as e:
            logger.error(f"Error getting call {call_id}: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/calls/<call_id>/terminate', methods=['POST'])
    def terminate_call(call_id):
        """Terminate a specific call"""
        try:
            success = app.call_service.terminate_call(call_id)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Call terminated successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to terminate call'
                }), 500
                
        except Exception as e:
            logger.error(f"Error terminating call {call_id}: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/calls/cleanup', methods=['POST'])
    def cleanup_calls():
        """Clean up stuck calls"""
        try:
            count = app.call_service.cleanup_stuck_calls()
            
            return jsonify({
                'success': True,
                'message': f'Cleaned up {count} stuck calls'
            })
            
        except Exception as e:
            logger.error(f"Error cleaning up calls: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/analytics/metrics', methods=['GET'])
    def get_analytics_metrics():
        """Get analytics metrics"""
        try:
            days = int(request.args.get('days', 30))
            metrics = app.call_service.get_analytics_metrics(days)
            
            return jsonify({
                'success': True,
                'metrics': metrics
            })
            
        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/config', methods=['GET'])
    def get_config():
        """Get current system configuration"""
        try:
            from ..config.settings import settings
            
            return jsonify({
                'success': True,
                'config': {
                    'synthflow_configured': bool(settings.synthflow.api_key),
                    'database_ready': True,  # If we got here, DB is working
                    'version': '2.0.0',
                    'features': {
                        'scheduling': True,
                        'bulk_operations': True,
                        'analytics': True
                    }
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting config: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500