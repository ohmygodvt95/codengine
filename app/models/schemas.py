"""
Pydantic schemas for request/response models.
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from app.config import settings


class File(BaseModel):
    """Represents a file to be executed."""
    name: str = Field(..., description="File name (can include relative path)")
    content: str = Field(..., description="File content")

    @validator('name')
    def validate_name(cls, v):
        if not v or v.strip() == "":
            raise ValueError("File name cannot be empty")
        if v.startswith('/'):
            raise ValueError("File name cannot be an absolute path")
        return v
    
    @validator('content')
    def validate_content_size(cls, v):
        size = len(v.encode('utf-8'))
        max_size = settings.max_file_size
        if size > max_size:
            raise ValueError(
                f"File content too large: {size} bytes. "
                f"Maximum allowed: {max_size} bytes ({max_size // 1024} KB)"
            )
        return v


class ExecRequest(BaseModel):
    """Request model for code execution."""
    language: str = Field(..., description="Programming language (e.g., 'python', 'node')")
    version: str = Field(..., description="Language version (e.g., '3.11.9', '3.12')")
    files: List[File] = Field(..., min_items=1, description="List of files to execute")
    stdin: str = Field(default="", description="Standard input for the program")
    args: List[str] = Field(default_factory=list, description="Command-line arguments")
    time_limit: float = Field(default=2.0, ge=0.1, le=30.0, description="Time limit in seconds")
    memory_limit: int = Field(default=256, ge=32, le=2048, description="Memory limit in MB")
    internet: bool = Field(default=False, description="Enable internet access in sandbox")

    @validator('language')
    def validate_language(cls, v):
        v = v.lower()
        supported = ['python', 'node']
        if v not in supported:
            raise ValueError(f"Language '{v}' not supported. Supported: {', '.join(supported)}")
        return v
    
    @validator('files')
    def validate_files_count_and_size(cls, v):
        # Check file count
        if len(v) > settings.max_files_count:
            raise ValueError(
                f"Too many files: {len(v)}. Maximum allowed: {settings.max_files_count}"
            )
        
        # Check total size
        total_size = sum(len(f.content.encode('utf-8')) for f in v)
        max_total = settings.max_total_files_size
        if total_size > max_total:
            raise ValueError(
                f"Total files size too large: {total_size} bytes. "
                f"Maximum allowed: {max_total} bytes ({max_total // 1024} KB)"
            )
        
        return v


class ExecResult(BaseModel):
    """Result model for code execution."""
    stdout: str = Field(default="", description="Standard output")
    stderr: str = Field(default="", description="Standard error")
    exit_code: int = Field(..., description="Exit code of the process")
    time: float = Field(..., description="Execution time in seconds")
    job_id: str = Field(..., description="Unique job identifier")
    error: Optional[str] = Field(default=None, description="Error message if execution failed")
