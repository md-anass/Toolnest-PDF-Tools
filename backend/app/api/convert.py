import os
import uuid
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.models.conversion import (
    UploadResponse,
    JobStatusResponse,
    DocumentAnalysis,
    JobStatus,
    ConversionStage,
)
from app.utils.file_validation import (
    validate_pdf_bytes,
    sanitize_filename,
    PDFValidationError,
    MAX_FILE_SIZE_BYTES,
)
from app.utils.cleanup import get_upload_path
from app.services.conversion_service import conversion_service, job_store
from app.services.pdf_analyzer import PDFAnalyzer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["conversion"])


@router.post("/convert", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_conversion_job(file: UploadFile = File(...)):
    """Upload a PDF file and start asynchronous conversion to editable DOCX."""
    raw_filename = file.filename or "document.pdf"
    clean_filename = sanitize_filename(raw_filename)

    # Read uploaded file content
    try:
        content = await file.read()
    except Exception as e:
        logger.error(f"Error reading uploaded file: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read the uploaded file. Please try again.",
        )

    file_size = len(content)

    # Security & format validation
    try:
        validate_pdf_bytes(content, clean_filename)
    except PDFValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.user_friendly_message,
        )
    except Exception as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to process this file. Please ensure it is a valid PDF.",
        )

    # Save to isolated temporary upload path
    file_id = str(uuid.uuid4())
    upload_path = get_upload_path(file_id)

    try:
        with open(upload_path, "wb") as f:
            f.write(content)
    except Exception as e:
        logger.error(f"Failed to write uploaded file to disk: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server failed to store uploaded document. Please retry.",
        )

    # Create conversion tracking job
    job_id = job_store.create_job(
        file_id=file_id,
        original_filename=clean_filename,
        file_size=file_size,
    )

    # Launch background conversion thread
    conversion_service.start_conversion_async(
        job_id=job_id,
        file_id=file_id,
        original_filename=clean_filename,
    )

    return UploadResponse(
        job_id=job_id,
        file_id=file_id,
        original_filename=clean_filename,
        file_size=file_size,
        status=JobStatus.PENDING,
        stage=ConversionStage.UPLOADING,
        message="PDF uploaded successfully. Processing started.",
    )


@router.get("/convert/{job_id}", response_model=JobStatusResponse)
async def get_conversion_status(job_id: str):
    """Retrieve current conversion status, progress, stage, and result."""
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversion job not found or has expired.",
        )

    return JobStatusResponse(
        job_id=job["job_id"],
        status=job["status"],
        stage=job["stage"],
        stage_message=job["stage_message"],
        progress=job["progress"],
        error_message=job["error_message"],
        result=job["result"],
        analysis=job["analysis"],
        created_at=job["created_at"],
        updated_at=job["updated_at"],
    )


@router.post("/analyze", response_model=DocumentAnalysis)
async def analyze_pdf(file: UploadFile = File(...)):
    """Pre-analyze an uploaded PDF to return page count, text density, and scanned status."""
    raw_filename = file.filename or "document.pdf"
    clean_filename = sanitize_filename(raw_filename)

    try:
        content = await file.read()
        validate_pdf_bytes(content, clean_filename)
    except PDFValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.user_friendly_message,
        )

    temp_id = f"preview_{uuid.uuid4()}"
    temp_path = get_upload_path(temp_id)

    try:
        with open(temp_path, "wb") as f:
            f.write(content)

        analysis = PDFAnalyzer.analyze_document(str(temp_path))
        return analysis
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to analyze this PDF. It may be encrypted or corrupted.",
        )
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass
