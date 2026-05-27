from datetime import datetime
import logging
import os
from typing import Optional

from dotenv import load_dotenv
import redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Application logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("webvory")

app = FastAPI(
    title="Webvory AI Backend",
    version="0.1.0",
    description="A minimal FastAPI backend with Docker, PostgreSQL, Redis, and NGINX reverse proxy.",
)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_client = redis.Redis.from_url(REDIS_URL, socket_timeout=2)

@app.get("/")
def root():
    """Root endpoint for quick local verification."""
    return {
        "service": "Webvory AI Backend",
        "status": "running",
        "health": "/health",
        "ready": "/ready",
        "predict": "/predict (POST)",
    }

class CompletionRequest(BaseModel):
    prompt: str
    max_tokens: Optional[int] = 128

class CompletionResponse(BaseModel):
    prompt: str
    completion: str
    model: str = "mini-ai"
    timestamp: str


@app.get("/health")
def health():
    """Health check endpoint for load balancers and container monitoring."""
    redis_status = False
    try:
        redis_status = redis_client.ping()
    except redis.RedisError as exc:
        logger.warning("Redis health check failed: %s", exc)

    return {
        "status": "ok" if redis_status else "degraded",
        "time": datetime.utcnow().isoformat() + "Z",
        "redis": redis_status,
    }


@app.get("/ready")
def ready():
    """Readiness endpoint to verify the backend can respond quickly."""
    return {"ready": True}


@app.post("/predict", response_model=CompletionResponse)
def predict(payload: CompletionRequest):
    """A simple placeholder AI-style completion endpoint."""
    if not payload.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt must not be empty")

    logger.info("Received prediction request")
    completion = f"Echo: {payload.prompt.strip()}"

    return CompletionResponse(
        prompt=payload.prompt,
        completion=completion,
        timestamp=datetime.utcnow().isoformat() + "Z",
    )
