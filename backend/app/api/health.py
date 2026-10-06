from fastapi import APIRouter
from app.models.conversion import HealthResponse
from app.services.ocr_service import ocr_service

router = APIRouter(prefix="", tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check backend operational health and OCR engine readiness."""
    is_available = ocr_service.is_ocr_available()
    engine_name = ocr_service.get_engine_name()
    version = ocr_service.get_version()

    return HealthResponse(
        status="ok",
        service="PDF to Word Conversion Engine",
        version="1.0.0",
        ocr_available=is_available,
        ocr_engine=engine_name,
        tesseract_version=version,
    )
