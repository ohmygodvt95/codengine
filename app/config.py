"""
Configuration management for the code execution engine.
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # API Settings
    api_title: str = "Code Execution Engine"
    api_version: str = "2.0.0"
    api_description: str = "A secure code execution engine similar to Piston"
    
    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # Execution Limits
    max_time_limit: float = 300.0
    max_memory_limit: int = 2048
    default_time_limit: float = 30.0
    default_memory_limit: int = 128
    
    # File Size Limits (in bytes)
    max_file_size: int = 1024 * 1024  # 1 MB per file
    max_total_files_size: int = 5 * 1024 * 1024  # 5 MB total
    max_files_count: int = 10  # Maximum number of files
    
    # Output Limits (in bytes)
    max_output_size: int = 256 * 1024  # 256 KB for stdout
    max_stderr_size: int = 256 * 1024  # 256 KB for stderr
    
    # Runtime Settings
    packages_dir: str = "/packages"
    
    # Sandbox Settings
    use_bubblewrap: bool = True  # Set to False to force direct mode (less secure)
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
