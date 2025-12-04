"""
FastAPI application initialization.
"""
import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.routes import router
from app.exceptions import CodeEngineException


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        description=settings.api_description
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(router)
    
    # Exception handlers
    @app.exception_handler(CodeEngineException)
    async def code_engine_exception_handler(request, exc: CodeEngineException):
        """Handle CodeEngineException."""
        return JSONResponse(
            status_code=500,
            content={"error": str(exc)}
        )
    
    return app


# Create app instance
app = create_app()
