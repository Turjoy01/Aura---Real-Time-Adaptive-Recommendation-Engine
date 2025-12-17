from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from src.core.config import settings
from src.db.mongodb import connect_to_mongo, close_mongo_connection
from src.routers import behavior, recommend, user

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting Aura Recommendation Engine...")
    await connect_to_mongo()
    logger.info("✓ Service initialized")
    yield
    # Shutdown
    logger.info("🛑 Shutting down...")
    await close_mongo_connection()
    logger.info("✓ Service stopped")

# Initialize FastAPI app
app = FastAPI(
    title="Aura - Real-Time Adaptive Recommendation Engine",
    description="Real-time, reinforcement-learning-powered personalization engine for event recommendations",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(behavior.router)
app.include_router(recommend.router)
app.include_router(user.router)

@app.get(
    "/v1/health",
    tags=["Health"],
    summary="Health Check",
    description="Service health status endpoint"
)
async def health_check() -> dict:
    """
    **Health check endpoint** - returns 200 if service is running
    
    Used for:
    - Load balancer health checks
    - Deployment verification
    - Monitoring and alerting
    """
    return {
        "status": "healthy",
        "service": "VENTYY Recommendation Microservice",
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0"
    }

# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "detail": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "detail": "Internal server error",
            "status_code": 500
        }
    )

# Welcome endpoint
@app.get(
    "/",
    tags=["Root"],
    summary="API Root",
    description="Welcome to Aura Recommendation Engine"
)
async def root() -> dict:
    """
    **Welcome to Aura!**
    
    This microservice powers personalized event recommendations with real-time learning.
    
    **Key features:**
    - ✓ Sub-300ms recommendations at 100K DAU
    - ✓ Real-time reinforcement learning (no batch jobs)
    - ✓ Cold-start smart recommendations
    - ✓ Natural language search with LLM
    - ✓ Multi-armed bandit algorithm
    
    **Get started:**
    1. Visit `/docs` for interactive Swagger UI
    2. Generate a JWT token from main auth service
    3. Use token in Authorization header: `Bearer <your-token>`
    4. Test endpoints in Swagger UI
    
    **Main endpoints:**
    - `POST /v1/behavior/log` - Log user actions
    - `POST /v1/recommend/feed` - Get personalized feed
    - `POST /v1/recommend/natural` - Natural language search
    - `POST /v1/recommend/highlights` - Get trending highlights
    - `GET /v1/user/profile` - View your preference profile
    """
    return {
        "service": "Aura Recommendation Engine",
        "version": "1.0.0",
        "docs": "Visit /docs for Swagger UI",
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.SERVICE_HOST,
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
