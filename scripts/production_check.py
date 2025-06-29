#!/usr/bin/env python3
"""
Production Readiness Check

This script validates that the system is properly configured
and ready for production deployment.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple

def check_python_version() -> Tuple[bool, str]:
    """Check if Python version is 3.11+"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        return True, f"✅ Python {version.major}.{version.minor}.{version.micro}"
    else:
        return False, f"❌ Python {version.major}.{version.minor}.{version.micro} (requires 3.11+)"

def check_environment_variables() -> Tuple[bool, List[str]]:
    """Check required environment variables"""
    required_vars = [
        'SYNTHFLOW_API_KEY',
        'SECRET_KEY',
        'SYNTHFLOW_ASSISTANT_ID',
        'SYNTHFLOW_PHONE_NUMBER'
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        return False, [f"❌ Missing: {var}" for var in missing]
    else:
        return True, ["✅ All required environment variables set"]

def check_dependencies() -> Tuple[bool, str]:
    """Check if all dependencies are installed"""
    try:
        import flask
        import flask_socketio
        import requests
        import aiohttp
        import pytest
        return True, "✅ All dependencies installed"
    except ImportError as e:
        return False, f"❌ Missing dependency: {e}"

def check_database() -> Tuple[bool, str]:
    """Check database connectivity"""
    try:
        from src.core.database import DatabaseService
        from src.config.settings import settings
        
        db = DatabaseService(settings.database.path)
        # Try to get calls (will create tables if needed)
        db.get_calls(limit=1)
        return True, "✅ Database accessible"
    except Exception as e:
        return False, f"❌ Database error: {e}"

def check_synthflow_api() -> Tuple[bool, str]:
    """Check Synthflow API connectivity"""
    try:
        from src.config.settings import settings
        import requests
        
        headers = {
            "Authorization": f"Bearer {settings.synthflow.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{settings.synthflow.base_url}/assistants",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return True, "✅ Synthflow API accessible"
        else:
            return False, f"❌ Synthflow API error: {response.status_code}"
            
    except Exception as e:
        return False, f"❌ Synthflow API connection failed: {e}"

def check_security_config() -> Tuple[bool, List[str]]:
    """Check security configuration"""
    issues = []
    
    # Check SECRET_KEY
    secret_key = os.getenv('SECRET_KEY', '')
    if not secret_key or secret_key == 'your-secret-key':
        issues.append("❌ SECRET_KEY not set or using default value")
    elif len(secret_key) < 32:
        issues.append("⚠️  SECRET_KEY should be at least 32 characters")
    else:
        issues.append("✅ SECRET_KEY properly configured")
    
    # Check DEBUG setting
    debug = os.getenv('DEBUG', 'False').lower()
    if debug == 'true':
        issues.append("⚠️  DEBUG is enabled (should be False in production)")
    else:
        issues.append("✅ DEBUG disabled")
    
    # Check ENVIRONMENT
    environment = os.getenv('ENVIRONMENT', 'development')
    if environment != 'production':
        issues.append(f"⚠️  ENVIRONMENT is '{environment}' (should be 'production')")
    else:
        issues.append("✅ ENVIRONMENT set to production")
    
    return len([i for i in issues if i.startswith('❌')]) == 0, issues

def check_file_permissions() -> Tuple[bool, List[str]]:
    """Check file and directory permissions"""
    checks = []
    
    # Check data directory
    data_dir = Path("data")
    if data_dir.exists():
        if os.access(data_dir, os.W_OK):
            checks.append("✅ Data directory writable")
        else:
            checks.append("❌ Data directory not writable")
    else:
        try:
            data_dir.mkdir(parents=True, exist_ok=True)
            checks.append("✅ Data directory created")
        except Exception as e:
            checks.append(f"❌ Cannot create data directory: {e}")
    
    # Check logs directory
    logs_dir = Path("logs")
    if logs_dir.exists():
        if os.access(logs_dir, os.W_OK):
            checks.append("✅ Logs directory writable")
        else:
            checks.append("❌ Logs directory not writable")
    else:
        try:
            logs_dir.mkdir(parents=True, exist_ok=True)
            checks.append("✅ Logs directory created")
        except Exception as e:
            checks.append(f"❌ Cannot create logs directory: {e}")
    
    return len([c for c in checks if c.startswith('❌')]) == 0, checks

def run_tests() -> Tuple[bool, str]:
    """Run test suite"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return True, "✅ All tests passed"
        else:
            return False, f"❌ Tests failed:\n{result.stdout}\n{result.stderr}"
            
    except subprocess.TimeoutExpired:
        return False, "❌ Tests timed out"
    except FileNotFoundError:
        return False, "⚠️  Tests not found (pytest not available)"
    except Exception as e:
        return False, f"❌ Test execution error: {e}"

def main():
    """Run all production readiness checks"""
    print("🔍 Production Readiness Check")
    print("=" * 50)
    
    checks = [
        ("Python Version", check_python_version),
        ("Environment Variables", check_environment_variables),
        ("Dependencies", check_dependencies),
        ("Database", check_database),
        ("Synthflow API", check_synthflow_api),
        ("Security Configuration", check_security_config),
        ("File Permissions", check_file_permissions),
        ("Test Suite", run_tests)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}")
        print("-" * 30)
        
        try:
            result = check_func()
            
            if isinstance(result, tuple) and len(result) == 2:
                passed, message = result
                
                if isinstance(message, list):
                    for msg in message:
                        print(f"  {msg}")
                else:
                    print(f"  {message}")
                
                if not passed:
                    all_passed = False
            else:
                print(f"  ❌ Check function returned unexpected result: {result}")
                all_passed = False
                
        except Exception as e:
            print(f"  ❌ Check failed with exception: {e}")
            all_passed = False
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("🎉 PRODUCTION READY!")
        print("✅ All checks passed. System is ready for production deployment.")
        print("\nNext steps:")
        print("1. Deploy using: ./scripts/deploy.sh")
        print("2. Monitor logs: tail -f logs/app.log")
        print("3. Check health: curl http://localhost:5000/health")
        return 0
    else:
        print("❌ PRODUCTION NOT READY")
        print("⚠️  Please fix the issues above before deploying to production.")
        print("\nCommon fixes:")
        print("1. Set environment variables in .env file")
        print("2. Install missing dependencies: pip install -r requirements-updated.txt")
        print("3. Check Synthflow account and API key")
        print("4. Ensure proper file permissions")
        return 1

if __name__ == "__main__":
    sys.exit(main())