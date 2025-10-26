from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and .env file.
    
    Uses Pydantic BaseSettings for type validation and automatic loading
    from .env files.
    """
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8080, description="Server port")
    
    # API Keys
    gemini_api_key: Optional[str] = Field(default=None, description="Google Gemini API key")


# Create a global settings instance
settings = Settings()


# Legacy compatibility functions for existing code
def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get an environment variable value.
    
    Legacy compatibility function. Uses settings instance.
    
    Args:
        key: The environment variable key
        default: Default value if the key is not found
        
    Returns:
        The environment variable value or default
    """
    key_lower = key.lower()
    if hasattr(settings, key_lower):
        value = getattr(settings, key_lower)
        return value if value is not None else default
    return default


def get_host() -> str:
    """Get host from environment variable or use default"""
    return settings.host


def get_port() -> int:
    """Get port from environment variable or use default"""
    return settings.port


# Environment variable key constants (for backward compatibility)
ENV_HOST = "HOST"
ENV_PORT = "PORT"
ENV_GEMINI_API_KEY = "GEMINI_API_KEY"