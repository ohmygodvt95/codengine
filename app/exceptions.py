"""
Custom exceptions for the code execution engine.
"""


class CodeEngineException(Exception):
    """Base exception for code engine errors."""
    pass


class RuntimeNotFoundException(CodeEngineException):
    """Raised when the requested runtime is not found."""
    pass


class UnsupportedLanguageException(CodeEngineException):
    """Raised when the requested language is not supported."""
    pass


class SandboxExecutionException(CodeEngineException):
    """Raised when execution in sandbox fails."""
    pass


class ResourceLimitException(CodeEngineException):
    """Raised when resource limits are exceeded."""
    pass


class FileSystemException(CodeEngineException):
    """Raised when file system operations fail."""
    pass
