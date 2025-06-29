"""
Core business services for call management

This module contains the main business logic for managing calls,
integrating with external APIs, and coordinating system operations.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor

from .models import Call, CallRequest, CallStatus
from .database import DatabaseService
from ..api.synthflow_client import AsyncSynthflowClient
from ..api.exceptions import SynthflowAPIException
from ..utils.logging import get_logger

logger = get_logger(__name__)

class CallService:
    """Main service for call management operations"""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self._executor = ThreadPoolExecutor(max_workers=10)
    
    def initiate_call(self, call: Call) -> bool:
        """
        Initiate a new call
        
        Args:
            call: Call object to initiate
            
        Returns:
            bool: True if call was successfully initiated
        """
        try:
            # Validate call request
            call.request.validate()
            
            # Save call to database
            if not self.db_service.save_call(call):
                logger.error(f"Failed to save call {call.id} to database")
                return False
            
            # Start async call processing
            asyncio.create_task(self._process_call_async(call))
            
            logger.info(f"Call {call.id} initiated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initiate call {call.id}: {e}")
            self._update_call_status(call.id, CallStatus.FAILED, error_message=str(e))
            return False
    
    async def _process_call_async(self, call: Call):
        """Process call asynchronously with Synthflow API"""
        try:
            # Update status to initiating
            self._update_call_status(call.id, CallStatus.INITIATING)
            
            # Create call with Synthflow
            async with AsyncSynthflowClient() as client:
                result = await client.create_call(call)
                
                if result.get('status') == 'ok':
                    synthflow_call_id = result.get('response', {}).get('call_id')
                    
                    # Update call with Synthflow ID
                    updates = {
                        'status': CallStatus.DIALING,
                        'synthflow_call_id': synthflow_call_id
                    }
                    self.db_service.update_call(call.id, updates)
                    
                    # Monitor call progress
                    await self._monitor_call_progress(call.id, synthflow_call_id, client)
                    
                else:
                    raise SynthflowAPIException(f"Call creation failed: {result}")
                    
        except Exception as e:
            logger.error(f"Error processing call {call.id}: {e}")
            self._update_call_status(
                call.id, 
                CallStatus.FAILED, 
                error_message=str(e),
                completed_at=datetime.now()
            )
    
    async def _monitor_call_progress(self, call_id: str, synthflow_call_id: str, client: AsyncSynthflowClient):
        """Monitor call progress and update status"""
        max_polls = 24  # 2 minutes (24 x 5 seconds)
        poll_count = 0
        
        while poll_count < max_polls:
            try:
                await asyncio.sleep(5)  # Poll every 5 seconds
                poll_count += 1
                
                # Get call status from Synthflow
                status_result = await client.get_call_status(synthflow_call_id)
                
                # Extract status from response
                call_status = self._extract_call_status(status_result)
                
                # Update database
                self._update_call_status(call_id, call_status)
                
                # Check if call is completed
                if call_status in [CallStatus.COMPLETED, CallStatus.FAILED, 
                                 CallStatus.NO_ANSWER, CallStatus.BUSY]:
                    
                    # Get final transcript and analyze success
                    transcript = await self._get_call_transcript(synthflow_call_id, client)
                    success = self._analyze_call_success(transcript)
                    
                    # Final update
                    final_updates = {
                        'status': call_status,
                        'completed_at': datetime.now(),
                        'transcript': transcript,
                        'success': success
                    }
                    self.db_service.update_call(call_id, final_updates)
                    
                    logger.info(f"Call {call_id} completed with status: {call_status}")
                    break
                    
            except Exception as e:
                logger.warning(f"Error monitoring call {call_id}: {e}")
                continue
        
        # Handle timeout
        if poll_count >= max_polls:
            logger.warning(f"Call {call_id} monitoring timeout")
            self._update_call_status(
                call_id, 
                CallStatus.FAILED, 
                error_message="Monitoring timeout",
                completed_at=datetime.now()
            )
    
    def _extract_call_status(self, status_result: Dict[str, Any]) -> CallStatus:
        """Extract call status from Synthflow API response"""
        try:
            if 'calls' in status_result.get('response', {}):
                calls = status_result['response']['calls']
                if calls and len(calls) > 0:
                    status_str = calls[0].get('status', 'unknown')
                    return CallStatus(status_str)
            
            # Fallback to direct status field
            status_str = status_result.get('status', 'unknown')
            return CallStatus(status_str) if status_str in CallStatus.__members__.values() else CallStatus.FAILED
            
        except (KeyError, ValueError):
            return CallStatus.FAILED
    
    async def _get_call_transcript(self, synthflow_call_id: str, client: AsyncSynthflowClient) -> str:
        """Get call transcript from Synthflow"""
        try:
            transcript_result = await client.get_call_transcript(synthflow_call_id)
            return transcript_result.get('transcript', '')
        except Exception as e:
            logger.warning(f"Failed to get transcript for {synthflow_call_id}: {e}")
            return ""
    
    def _analyze_call_success(self, transcript: str) -> bool:
        """Analyze transcript to determine call success"""
        if not transcript:
            return False
        
        transcript_lower = transcript.lower()
        
        # Success indicators
        success_phrases = [
            "account adjusted", "adjustment made", "change completed",
            "updated successfully", "modification complete", "done",
            "processed", "completed", "confirmed", "yes, that's done",
            "request processed", "change applied", "update complete"
        ]
        
        # Failure indicators
        failure_phrases = [
            "cannot do that", "unable to", "not authorized", "need verification",
            "callback required", "supervisor needed", "system down",
            "not possible", "denied", "rejected", "error occurred"
        ]
        
        success_score = sum(1 for phrase in success_phrases if phrase in transcript_lower)
        failure_score = sum(1 for phrase in failure_phrases if phrase in transcript_lower)
        
        return success_score > failure_score
    
    def _update_call_status(self, call_id: str, status: CallStatus, 
                          error_message: Optional[str] = None,
                          completed_at: Optional[datetime] = None):
        """Update call status in database"""
        updates = {'status': status}
        
        if error_message:
            updates['error_message'] = error_message
        
        if completed_at:
            updates['completed_at'] = completed_at
        
        self.db_service.update_call(call_id, updates)
    
    def get_call(self, call_id: str) -> Optional[Call]:
        """Get call by ID"""
        return self.db_service.get_call(call_id)
    
    def get_calls(self, limit: int = 50, offset: int = 0, 
                  status_filter: Optional[str] = None) -> List[Call]:
        """Get calls with pagination and filtering"""
        status_enum = None
        if status_filter:
            try:
                status_enum = CallStatus(status_filter)
            except ValueError:
                logger.warning(f"Invalid status filter: {status_filter}")
        
        return self.db_service.get_calls(
            limit=limit, 
            offset=offset, 
            status_filter=status_enum
        )
    
    def terminate_call(self, call_id: str) -> bool:
        """Terminate an active call"""
        try:
            call = self.get_call(call_id)
            if not call:
                logger.error(f"Call {call_id} not found")
                return False
            
            if call.status not in [CallStatus.DIALING, CallStatus.IN_PROGRESS]:
                logger.warning(f"Call {call_id} is not active (status: {call.status})")
                return False
            
            # Update status to terminated
            updates = {
                'status': CallStatus.TERMINATED,
                'completed_at': datetime.now()
            }
            
            success = self.db_service.update_call(call_id, updates)
            
            if success:
                logger.info(f"Call {call_id} terminated successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Error terminating call {call_id}: {e}")
            return False
    
    def cleanup_stuck_calls(self) -> int:
        """Clean up calls that are stuck in progress"""
        try:
            # Find calls stuck in progress for more than 30 minutes
            cutoff_time = datetime.now() - timedelta(minutes=30)
            
            stuck_calls = []
            all_calls = self.get_calls(limit=1000)  # Get large batch
            
            for call in all_calls:
                if (call.status in [CallStatus.DIALING, CallStatus.IN_PROGRESS, CallStatus.INITIATING] 
                    and call.created_at < cutoff_time):
                    stuck_calls.append(call)
            
            # Update stuck calls to timeout status
            count = 0
            for call in stuck_calls:
                updates = {
                    'status': CallStatus.FAILED,
                    'error_message': 'Call timeout - automatically cleaned up',
                    'completed_at': datetime.now()
                }
                
                if self.db_service.update_call(call.id, updates):
                    count += 1
            
            logger.info(f"Cleaned up {count} stuck calls")
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up stuck calls: {e}")
            return 0
    
    def get_analytics_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Get analytics metrics for the specified period"""
        try:
            from .analytics import AnalyticsService
            
            analytics = AnalyticsService(self.db_service)
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Get metrics
            metrics = analytics.get_call_metrics(start_date, end_date)
            success_trend = analytics.get_success_rate_trend(days)
            volume_by_hour = analytics.get_call_volume_by_hour(days)
            failure_reasons = analytics.get_top_failure_reasons()
            
            return {
                'period_days': days,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'metrics': {
                    'total_calls': metrics.total_calls,
                    'successful_calls': metrics.successful_calls,
                    'failed_calls': metrics.failed_calls,
                    'success_rate': metrics.success_rate,
                    'average_duration': metrics.average_duration,
                    'total_duration': metrics.total_duration
                },
                'trends': {
                    'success_rate': [
                        {
                            'date': point.timestamp.isoformat(),
                            'value': point.value,
                            'label': point.label
                        }
                        for point in success_trend
                    ],
                    'volume_by_hour': [
                        {
                            'hour': point.label,
                            'count': point.value
                        }
                        for point in volume_by_hour
                    ]
                },
                'failure_analysis': failure_reasons
            }
            
        except Exception as e:
            logger.error(f"Error getting analytics metrics: {e}")
            return {
                'error': str(e),
                'period_days': days,
                'metrics': {
                    'total_calls': 0,
                    'successful_calls': 0,
                    'failed_calls': 0,
                    'success_rate': 0.0,
                    'average_duration': 0.0,
                    'total_duration': 0
                }
            }
    
    def create_bulk_calls(self, call_requests: List[CallRequest]) -> List[str]:
        """Create multiple calls in bulk"""
        created_call_ids = []
        
        for request in call_requests:
            try:
                call = Call(
                    id=str(uuid.uuid4()),
                    request=request
                )
                
                if self.initiate_call(call):
                    created_call_ids.append(call.id)
                    
            except Exception as e:
                logger.error(f"Failed to create bulk call for {request.caller_name}: {e}")
                continue
        
        logger.info(f"Created {len(created_call_ids)} calls out of {len(call_requests)} requests")
        return created_call_ids