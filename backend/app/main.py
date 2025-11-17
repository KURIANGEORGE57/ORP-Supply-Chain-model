# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .api.v1 import assertions, evaluations, enactments
from .utils.logging import logger

app = FastAPI(
    title=settings.APP_NAME,
    description="Open Registry Protocol (ORP) Supply Chain Backend",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    assertions.router,
    prefix="/api/v1/assertions",
    tags=["assertions"]
)

app.include_router(
    evaluations.router,
    prefix="/api/v1",
    tags=["evaluations"]
)

app.include_router(
    enactments.router,
    prefix="/api/v1",
    tags=["enactments"]
)

@app.get("/")
def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
