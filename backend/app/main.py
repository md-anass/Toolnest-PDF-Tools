import time
import logging
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api import convert_router, files_router, health_router, tools_router
from app.utils.cleanup import clean_stale_files, UPLOAD_DIR, OUTPUT_DIR
from app.services.ocr_service import ocr_service

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("toolnest")

# Background cleanup thread controller
_stop_cleanup_event = threading.Event()


def periodic_cleanup_worker():
    """Background worker periodically clearing temporary files older than 30 minutes."""
    logger.info("Starting background temporary file cleanup worker.")
    while not _stop_cleanup_event.is_set():
        try:
            # Clean files older than 1800s (30 mins)
            cleaned = clean_stale_files(max_age_seconds=1800)
            if cleaned > 0:
                logger.info(f"Periodic cleanup removed {cleaned} expired temporary files.")
        except Exception as e:
            logger.warning(f"Error during periodic cleanup: {e}")

        # Sleep in 5-second intervals to allow responsive shutdown
        for _ in range(120):  # 120 * 5s = 600s = 10 minutes
            if _stop_cleanup_event.is_set():
                break
            time.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure dirs exist, start cleanup worker, verify OCR
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    ocr_available = ocr_service.is_ocr_available()
    engine_name = ocr_service.get_engine_name()
    logger.info(f"PDF to Word API started. OCR Engine: {engine_name} (Available: {ocr_available})")

    cleanup_thread = threading.Thread(target=periodic_cleanup_worker, daemon=True)
    cleanup_thread.start()

    yield

    # Shutdown
    _stop_cleanup_event.set()
    logger.info("Shutting down PDF to Word API and cleanup worker.")


app = FastAPI(
    title="Toolnest PDF and Document Tools API",
    description="PDF merge, split, compression, document conversion, and OCR-powered PDF to Word tools.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """Uniform human-readable error response format without exposing internal traces."""
    detail = exc.detail if isinstance(exc.detail, str) else "An unexpected error occurred."
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "message": detail,
        },
    )


# Register API endpoints
app.include_router(convert_router, prefix="/api")
app.include_router(files_router, prefix="/api")
app.include_router(health_router, prefix="/api")
app.include_router(tools_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "service": "Toolnest PDF and Document Tools",
        "status": "online",
        "docs_url": "/docs",
        "health_url": "/api/health",
    }
