"""
API route handlers.
"""
import logging
import os
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.models import ExecRequest, ExecResult
from app.core import CodeExecutor, RuntimeManager, SandboxManager
from app.exceptions import CodeEngineException

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize executor
executor = CodeExecutor()


@router.get("/")
async def root():
    """Root endpoint."""
    from app.config import settings
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "status": "running"
    }


@router.get("/api/v2/runtimes")
async def get_runtimes():
    """Get available runtimes."""
    runtimes = []
    
    for language, config in RuntimeManager.SUPPORTED_LANGUAGES.items():
        base_dir = config['base_dir']
        if os.path.isdir(base_dir):
            versions = [
                d for d in os.listdir(base_dir)
                if os.path.isdir(os.path.join(base_dir, d))
            ]
            for version in sorted(versions):
                runtimes.append({
                    "language": language,
                    "version": version,
                    "runtime": f"{language}-{version}"
                })
    
    return {"runtimes": runtimes}


@router.post("/api/v2/execute", response_model=ExecResult)
async def execute(request: ExecRequest):
    """
    Execute code in a sandboxed environment.
    
    Args:
        request: ExecRequest containing code and execution parameters
        
    Returns:
        ExecResult with execution output and metadata
    """
    try:
        result = executor.execute_code(request)
        return result
        
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except CodeEngineException as e:
        logger.error(f"Code engine error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.exception("Unexpected error in execute endpoint")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    bwrap_available = SandboxManager.validate_bubblewrap_available()
    bwrap_working = SandboxManager.check_bubblewrap_working() if bwrap_available else False
    
    if bwrap_working:
        status = "healthy"
        mode = "sandboxed (bubblewrap)"
    elif bwrap_available:
        status = "degraded"
        mode = "direct (bubblewrap installed but not working)"
    else:
        status = "degraded"
        mode = "direct (bubblewrap not installed)"
    
    return {
        "status": status,
        "execution_mode": mode,
        "bubblewrap_installed": bwrap_available,
        "bubblewrap_working": bwrap_working
    }
