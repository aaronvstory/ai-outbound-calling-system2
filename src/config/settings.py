"""
Application settings and configuration management

This module handles all configuration through environment variables
with sensible defaults and validation.
"""

import os
from typing import Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    path: str
    backup_interval: int = 3600
    max_connections: int = 10
    timeout: int = 30

@dataclass
class SynthflowConfig:
    """Synthflow API configuration settings"""
    api_key: str
    base_url: str = "https://api.synthflow.ai/v2"
    timeout: int = 30
    retry_attempts: int = 3
    assistant_id: Optional[str] = None
    phone_number: Optional[str] = None

@dataclass
class AppConfig:
    """Flask application configuration"""
    secret_key: str
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 5000
    log_level: str = "INFO"
    environment: str = "development"

@dataclass
class RedisConfig:
    """Redis configuration for caching and job queue"""
    url: str = "redis://localhost:6379/0"
    enabled: bool = False

@dataclass
class SecurityConfig:
    """Security-related configuration"""
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60
    cors_origins: str = "*"
    jwt_secret_key: Optional[str] = None
    jwt_access_token_expires: int = 3600

@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration"""
    sentry_dsn: Optional[str] = None
    metrics_enabled: bool = True
    metrics_port: int = 9090
    structured_logging: bool = True

class Settings:
    """Main settings class that loads configuration from environment"""
    
    def __init__(self):
        # Load environment variables
        self._load_env_file()
        
        # Initialize configuration sections
        self.database = DatabaseConfig(
            path=os.getenv("DATABASE_PATH", "data/calls.db"),
            backup_interval=int(os.getenv("DB_BACKUP_INTERVAL", "3600")),
            max_connections=int(os.getenv("DB_MAX_CONNECTIONS", "10")),
            timeout=int(os.getenv("DB_TIMEOUT", "30"))
        )
        
        self.synthflow = SynthflowConfig(
            api_key=self._get_required_env("SYNTHFLOW_API_KEY"),
            base_url=os.getenv("SYNTHFLOW_BASE_URL", "https://api.synthflow.ai/v2"),
            timeout=int(os.getenv("SYNTHFLOW_TIMEOUT", "30")),
            retry_attempts=int(os.getenv("SYNTHFLOW_RETRY_ATTEMPTS", "3")),
            assistant_id=os.getenv("SYNTHFLOW_ASSISTANT_ID"),
            phone_number=os.getenv("SYNTHFLOW_PHONE_NUMBER")
        )
        
        self.app = AppConfig(
            secret_key=self._get_required_env("SECRET_KEY"),
            debug=os.getenv("DEBUG", "False").lower() == "true",
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "5000")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            environment=os.getenv("ENVIRONMENT", "development")
        )
        
        self.redis = RedisConfig(
            url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            enabled=os.getenv("REDIS_ENABLED", "False").lower() == "true"
        )
        
        self.security = SecurityConfig(
            rate_limit_enabled=os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true",
            rate_limit_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")),
            cors_origins=os.getenv("CORS_ORIGINS", "*"),
            jwt_secret_key=os.getenv("JWT_SECRET_KEY"),
            jwt_access_token_expires=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "3600"))
        )
        
        self.monitoring = MonitoringConfig(
            sentry_dsn=os.getenv("SENTRY_DSN"),
            metrics_enabled=os.getenv("METRICS_ENABLED", "True").lower() == "true",
            metrics_port=int(os.getenv("METRICS_PORT", "9090")),
            structured_logging=os.getenv("STRUCTURED_LOGGING", "True").lower() == "true"
        )
    
    def _load_env_file(self):
        """Load environment variables from .env file if it exists"""
        env_file = Path(".env")
        if env_file.exists():
            try:
                from dotenv import load_dotenv
                load_dotenv(env_file)
            except ImportError:
                # python-dotenv not installed, skip loading
                pass
    
    def _get_required_env(self, key: str) -> str:
        """Get required environment variable or raise error"""
        value = os.getenv(key)
        if not value:
            raise ValueError(
                f"Required environment variable {key} is not set. "
                f"Please check your .env file or environment configuration."
            )
        return value
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.app.environment.lower() == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.app.environment.lower() == "development"
    
    def validate(self) -> list[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        # Validate Synthflow configuration
        if not self.synthflow.api_key:
            errors.append("SYNTHFLOW_API_KEY is required")
        
        if not self.synthflow.assistant_id:
            errors.append("SYNTHFLOW_ASSISTANT_ID is required for call creation")
        
        if not self.synthflow.phone_number:
            errors.append("SYNTHFLOW_PHONE_NUMBER is required for outbound calls")
        
        # Validate app configuration
        if not self.app.secret_key or self.app.secret_key == "your-secret-key":
            errors.append("SECRET_KEY must be set to a secure random value")
        
        # Validate database path
        db_dir = Path(self.database.path).parent
        if not db_dir.exists():
            try:
                db_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create database directory: {e}")
        
        # Production-specific validations
        if self.is_production():
            if self.app.debug:
                errors.append("DEBUG should be False in production")
            
            if self.app.secret_key == "your-secret-key":
                errors.append("SECRET_KEY must be changed from default in production")
            
            if not self.monitoring.sentry_dsn:
                errors.append("SENTRY_DSN should be configured for production error tracking")
        
        return errors

# Global settings instance
settings = Settings()

# Validate settings on import
validation_errors = settings.validate()
if validation_errors:
    error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in validation_errors)
    if settings.is_production():
        raise ValueError(error_msg)
    else:
        print(f"⚠️  Configuration warnings:\n{error_msg}")