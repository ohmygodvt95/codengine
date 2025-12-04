"""
Code Execution Engine - Entry Point

A secure, sandboxed code execution engine similar to Piston.
Built with FastAPI and bubblewrap for containerization.
"""
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

if __name__ == "__main__":
    import uvicorn
    from app.config import settings
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
