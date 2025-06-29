"""
Input validation utilities
"""
import re
from typing import Dict, List, Any

def validate_call_request(data: Dict[str, Any]) -> List[str]:
    """Validate call request data"""
    errors = []
    
    # Required fields
    required_fields = ['caller_name', 'caller_phone', 'phone_number', 'account_action']
    for field in required_fields:
        if not data.get(field) or not str(data[field]).strip():
            errors.append(f'{field} is required')
    
    # Validate phone numbers
    if data.get('caller_phone'):
        if not validate_phone_number(data['caller_phone']):
            errors.append('caller_phone must be a valid phone number')
    
    if data.get('phone_number'):
        if not validate_phone_number(data['phone_number']):
            errors.append('phone_number must be a valid phone number')
    
    # Validate text lengths
    if data.get('caller_name') and len(data['caller_name']) > 100:
        errors.append('caller_name must be less than 100 characters')
    
    if data.get('account_action') and len(data['account_action']) > 1000:
        errors.append('account_action must be less than 1000 characters')
    
    if data.get('additional_info') and len(data['additional_info']) > 2000:
        errors.append('additional_info must be less than 2000 characters')
    
    return errors

def validate_phone_number(phone: str) -> bool:
    """Validate phone number format"""
    if not phone:
        return False
    
    # Remove common formatting characters
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # Basic validation - should start with + or digit and be 10-15 digits
    if re.match(r'^(\+?1?)?[0-9]{10,14}$', cleaned):
        return True
    
    return False

def validate_email(email: str) -> bool:
    """Validate email format"""
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def sanitize_input(text: str, max_length: int = None) -> str:
    """Sanitize text input"""
    if not text:
        return ""
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', str(text))
    
    # Trim whitespace
    sanitized = sanitized.strip()
    
    # Limit length if specified
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized