from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ConversionStage(str, Enum):
    UPLOADING = "uploading"
    ANALYZING = "analyzing"
    EXTRACTING = "extracting"
    RUNNING_OCR = "running_ocr"
    RECONSTRUCTING = "reconstructing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class PDFMetadata(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    creation_date: Optional[str] = None
    mod_date: Optional[str] = None


class PageAnalysis(BaseModel):
    page_number: int
    char_count: int
    word_count: int
    image_count: int
    table_count: int
    is_scanned: bool
    text_density: float = Field(
        ..., description="Characters per square point of page area"
    )
    has_selectable_text: bool


class DocumentAnalysis(BaseModel):
    page_count: int
    total_characters: int
    total_words: int
    total_images: int
    total_tables: int
    is_scanned: bool
    scanned_pages: List[int]
    selectable_pages: List[int]
    ocr_recommended: bool
    average_text_density: float
    metadata: PDFMetadata


class ExtractedElements(BaseModel):
    paragraphs: int = 0
    headings: int = 0
    tables: int = 0
    images: int = 0
    lists: int = 0


class ConversionResult(BaseModel):
    file_id: str
    job_id: str
    original_filename: str
    docx_filename: str
    download_url: str
    page_count: int
    is_scanned: bool
    ocr_used: bool
    extracted_elements: ExtractedElements
    duration_seconds: float
    file_size_bytes: int
    completed_at: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    stage: ConversionStage
    stage_message: str
    progress: int = Field(..., ge=0, le=100)
    error_message: Optional[str] = None
    result: Optional[ConversionResult] = None
    analysis: Optional[DocumentAnalysis] = None
    created_at: str
    updated_at: str


class UploadResponse(BaseModel):
    job_id: str
    file_id: str
    original_filename: str
    file_size: int
    status: JobStatus
    stage: ConversionStage
    message: str


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    ocr_available: bool
    ocr_engine: str
    tesseract_version: Optional[str] = None
