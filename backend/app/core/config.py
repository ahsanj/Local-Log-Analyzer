from pydantic_settings import BaseSettings
from typing import List, Union
import os


class Settings(BaseSettings):
    # App settings
    PROJECT_NAME: str = "Local Log Analyzer"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Privacy-first local log analysis application"
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    
    # CORS settings - use string to avoid pydantic parsing issues
    ALLOWED_ORIGINS_STR: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173"
    
    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        """Parse ALLOWED_ORIGINS from comma-separated string"""
        origins_str = os.getenv("ALLOWED_ORIGINS", self.ALLOWED_ORIGINS_STR)
        return [origin.strip() for origin in origins_str.split(",") if origin.strip()]
    
    # File upload settings
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    UPLOAD_DIR: str = "uploads"
    ALLOWED_EXTENSIONS: List[str] = [".log", ".txt", ".csv", ".syslog", ".json"]
    
    # Ollama settings
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "codellama:13b"
    OLLAMA_TIMEOUT: int = 120
    
    # Analysis settings
    MAX_LOG_ENTRIES: int = 100000
    PATTERN_DETECTION_THRESHOLD: float = 0.1
    ANOMALY_DETECTION_THRESHOLD: float = 2.0
    
    # Chat settings
    MAX_CHAT_HISTORY: int = 50
    CONTEXT_WINDOW_SIZE: int = 4000
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields


settings = Settings()