import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import get_settings
from models.database import create_all_tables
from services.redis_service import ping as redis_ping
from api.routes import research, workspaces, memory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────
    logger.info("Starting Atlas Research Agent backend…")

    # Create PostgreSQL tables
    try:
        await create_all_tables()
        logger.info("✓ Database tables ready")
    except Exception as e:
        logger.error(f"✗ Database setup failed: {e}")

    # Test Redis
    try:
        ok = await redis_ping()
        logger.info("✓ Redis connected" if ok else "✗ Redis ping failed")
    except Exception as e:
        logger.warning(f"✗ Redis unavailable: {e}")

    # Test ChromaDB
    try:
        host = settings.chroma_host.strip().lower() if settings.chroma_host else ""
        if host in ("local", "in_memory", "in-memory", ""):
            logger.info("✓ ChromaDB ready (local in-process mode)")
        else:
            import httpx
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    f"http://{settings.chroma_host}:{settings.chroma_port}/api/v2/heartbeat",
                    timeout=5,
                )
                logger.info("✓ ChromaDB connected" if r.status_code == 200 else "✗ ChromaDB heartbeat failed")
    except Exception as e:
        logger.warning(f"✗ ChromaDB unavailable: {e}")

    logger.info(f"Atlas Research Agent running on port {settings.backend_port}")
    yield
    # ── Shutdown ──────────────────────────────────────────
    logger.info("Shutting down Atlas Research Agent…")


app = FastAPI(
    title="Atlas Research Agent API",
    description="Autonomous multi-agent research platform",
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request logging middleware ─────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"→ {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"← {response.status_code} {request.url.path}")
    return response

# ── Global exception handler ──────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": str(exc)})

# ── Routers ───────────────────────────────────────────────
app.include_router(research.router)
app.include_router(workspaces.router)
app.include_router(memory.router)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "atlas-research-agent"}
