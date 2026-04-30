"""
Environment loader utility for multi-environment configuration.
Loads environment variables from .env.{APP_ENV} files.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class EnvironmentLoader:
    """Load and validate environment configuration for different deployment environments"""
    
    # Required settings per environment
    REQUIRED_SETTINGS = {
        "development": {
            "optional": ["SECRET_KEY", "SERVER_MONITORING_BOT_TOKEN"]  # Can be test values
        },
        "staging": {
            "required": ["SECRET_KEY", "SERVER_MONITORING_BOT_TOKEN", "TELEGRAM_WEBHOOK_URL"],
            "optional": []
        },
        "production": {
            "required": [
                "SECRET_KEY", "SERVER_MONITORING_BOT_TOKEN", "TELEGRAM_WEBHOOK_URL",
                "DATABASE_URL", "BACKEND_URL"
            ],
            "optional": []
        }
    }
    
    def __init__(self, app_env: Optional[str] = None):
        """
        Initialize environment loader
        
        Args:
            app_env: Environment name (development, staging, production).
                     If None, reads from APP_ENV or defaults to development.
        """
        self.app_env = app_env or os.getenv("APP_ENV", "development")
        self.project_root = Path(__file__).parent.parent
        self.env_file = self.project_root / f".env.{self.app_env}"
        self.env_values: Dict[str, Any] = {}
        
    def load(self) -> Dict[str, Any]:
        """
        Load environment variables from appropriate file
        
        Returns:
            Dictionary of loaded environment variables
            
        Raises:
            FileNotFoundError: If environment file doesn't exist
            ValueError: If required settings are missing
        """
        logger.info("Loading environment: %s from %s", self.app_env, self.env_file)
        
        if not self.env_file.exists():
            raise FileNotFoundError(
                f"Environment file not found: {self.env_file}. "
                f"Please create it or set APP_ENV to a valid environment."
            )
        
        # Load from file
        self._load_from_file()
        
        # Validate required settings
        self._validate_required_settings()
        
        # Set environment variables
        for key, value in self.env_values.items():
            os.environ[key] = str(value)
        
        logger.info("Environment loaded successfully. Configured for %s", self.app_env)
        return self.env_values
    
    def _load_from_file(self) -> None:
        """Load environment variables from .env file"""
        try:
            with open(self.env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    
                    # Skip comments and empty lines
                    if not line or line.startswith("#"):
                        continue
                    
                    # Parse KEY=VALUE
                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        self.env_values[key] = value
                        
        except IOError as e:
            raise IOError(
                f"Failed to read environment file {self.env_file}: {str(e)}"
            ) from e
    
    def _validate_required_settings(self) -> None:
        """Validate that required settings are present"""
        env_config = self.REQUIRED_SETTINGS.get(self.app_env, {})
        required = env_config.get("required", [])
        
        missing = []
        for key in required:
            if key not in self.env_values or not self.env_values[key]:
                missing.append(key)
        
        if missing:
            raise ValueError(
                f"Missing required settings for {self.app_env} environment: {', '.join(missing)}"
            )
        
        logger.info("All required settings validated for %s", self.app_env)
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get environment variable value
        
        Args:
            key: Setting key
            default: Default value if not found
            
        Returns:
            Setting value or default
        """
        return self.env_values.get(key, default)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all loaded environment variables"""
        return self.env_values.copy()


def load_environment(app_env: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to load environment
    
    Args:
        app_env: Environment name (development, staging, production)
        
    Returns:
        Dictionary of environment variables
    """
    loader = EnvironmentLoader(app_env)
    return loader.load()


if __name__ == "__main__":
    # Test environment loading
    try:
        env = load_environment()
        print(f"Loaded {len(env)} settings")
        print(f"Environment: {os.getenv('APP_ENV', 'development')}")
    except (FileNotFoundError, ValueError, IOError) as e:
        logger.error("Failed to load environment: %s", str(e))
