import os
import time
import uuid
import logging
import threading
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Optional, List
import fitz  # PyMuPDF
import pdfplumber

from app.models.conversion import (
    ConversionStage,
    JobStatus,
    JobStatusResponse,
    ConversionResult,
    DocumentAnalysis,
    ExtractedElements,
)
from app.utils.file_validation import validate_pdf_file_path, PDFValidationError
from app.utils.cleanup import (
    get_upload_path,
    get_output_path,
    delete_job_files,
    remove_file_safely,
)
from app.services.pdf_analyzer import PDFAnalyzer
from app.services.pdf_text_extractor import PDFTextExtractor, TextBlock
from app.services.image_extractor import ImageExtractor
from app.services.ocr_service import ocr_service
from app.services.layout_analyzer import LayoutAnalyzer, ExtractedTable
from app.services.docx_generator import DOCXGenerator

logger = logging.getLogger(__name__)


class JobStore:
    """Thread-safe in-memory job repository with status tracking."""

    def __init__(self):
        self._jobs: Dict[str, Dict] = {}
        self._lock = threading.Lock()

    def create_job(self, file_id: str, original_filename: str, file_size: int) -> str:
        job_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat() + "Z"
        with self._lock:
            self._jobs[job_id] = {
                "job_id": job_id,
                "file_id": file_id,
                "original_filename": original_filename,
                "file_size": file_size,
                "status": JobStatus.PENDING,
                "stage": ConversionStage.UPLOADING,
                "stage_message": "Uploading PDF...",
                "progress": 5,
                "error_message": None,
                "analysis": None,
                "result": None,
                "created_at": now,
                "updated_at": now,
                "start_time": time.time(),
            }
        return job_id

    def update_job(
        self,
        job_id: str,
        status: Optional[JobStatus] = None,
        stage: Optional[ConversionStage] = None,
        stage_message: Optional[str] = None,
        progress: Optional[int] = None,
        error_message: Optional[str] = None,
        analysis: Optional[DocumentAnalysis] = None,
        result: Optional[ConversionResult] = None,
    ):
        with self._lock:
            if job_id not in self._jobs:
                return
            job = self._jobs[job_id]
            if status is not None:
                job["status"] = status
            if stage is not None:
                job["stage"] = stage
            if stage_message is not None:
                job["stage_message"] = stage_message
            if progress is not None:
                job["progress"] = max(0, min(100, progress))
            if error_message is not None:
                job["error_message"] = error_message
            if analysis is not None:
                job["analysis"] = analysis
            if result is not None:
                job["result"] = result
            job["updated_at"] = datetime.now(timezone.utc).isoformat() + "Z"

    def get_job(self, job_id: str) -> Optional[Dict]:
        with self._lock:
            return self._jobs.get(job_id)

    def delete_job(self, job_id: str) -> bool:
        with self._lock:
            if job_id in self._jobs:
                del self._jobs[job_id]
                return True
            return False


# Global job repository singleton
job_store = JobStore()


class ConversionService:
    """Coordinates the full PDF to editable DOCX conversion pipeline."""

    def __init__(self, store: JobStore = job_store):
        self.store = store

    def start_conversion_async(self, job_id: str, file_id: str, original_filename: str):
        """Spawn background worker thread for non-blocking conversion."""
        thread = threading.Thread(
            target=self._process_conversion,
            args=(job_id, file_id, original_filename),
            daemon=True,
        )
        thread.start()

    def _process_conversion(self, job_id: str, file_id: str, original_filename: str):
        start_time = time.time()
        upload_path = get_upload_path(file_id)
        output_path = get_output_path(file_id)

        try:
            # 1. Validation
            self.store.update_job(
                job_id,
                status=JobStatus.PROCESSING,
                stage=ConversionStage.ANALYZING,
                stage_message="Validating and analyzing document structure...",
                progress=12,
            )

            validate_pdf_file_path(str(upload_path))

            # 2. PDF Analysis
            analysis = PDFAnalyzer.analyze_document(str(upload_path))
            self.store.update_job(
                job_id,
                stage=ConversionStage.ANALYZING,
                stage_message=f"Analyzed {analysis.page_count} pages ({len(analysis.scanned_pages)} scanned)",
                progress=25,
                analysis=analysis,
            )

            # 3. Document Processing (Text / OCR / Images / Tables)
            self.store.update_job(
                job_id,
                stage=ConversionStage.EXTRACTING,
                stage_message="Extracting document text and layout...",
                progress=35,
            )

            doc = fitz.open(str(upload_path))
            docx_gen = DOCXGenerator()
            ocr_was_used = False

            # Load tables with pdfplumber per page
            tables_by_page: Dict[int, List[ExtractedTable]] = {}
            try:
                with pdfplumber.open(str(upload_path)) as plum_pdf:
                    for p_idx, plum_page in enumerate(plum_pdf.pages):
                        page_num = p_idx + 1
                        raw_tables = plum_page.extract_tables() or []
                        table_objs = []
                        for tbl in raw_tables:
                            if not tbl or len(tbl) == 0:
                                continue
                            num_rows = len(tbl)
                            num_cols = max(len(r) for r in tbl)
                            # approximate bbox
                            tb_rect = fitz.Rect(54, 100, plum_page.width - 54, 300)
                            table_objs.append(
                                ExtractedTable(
                                    page_number=page_num,
                                    data=tbl,
                                    bbox=tb_rect,
                                    num_rows=num_rows,
                                    num_cols=num_cols,
                                )
                            )
                        tables_by_page[page_num] = table_objs
            except Exception as e:
                logger.warning(f"pdfplumber table loading warning: {e}")

            total_pages = doc.page_count
            for p_idx in range(total_pages):
                page_num = p_idx + 1
                page = doc[p_idx]
                page_width = page.rect.width

                is_page_scanned = page_num in analysis.scanned_pages

                # Progress calculation for extraction phase (35% to 70%)
                step_progress = int(35 + (35 * (page_num / total_pages)))

                if is_page_scanned:
                    # Stage 4: Running OCR
                    ocr_was_used = True
                    self.store.update_job(
                        job_id,
                        stage=ConversionStage.RUNNING_OCR,
                        stage_message=f"Running OCR on scanned page {page_num} of {total_pages}...",
                        progress=step_progress,
                    )
                    text_blocks = ocr_service.ocr_page(page)
                else:
                    self.store.update_job(
                        job_id,
                        stage=ConversionStage.EXTRACTING,
                        stage_message=f"Extracting content from page {page_num} of {total_pages}...",
                        progress=step_progress,
                    )
                    text_blocks = PDFTextExtractor.extract_blocks_from_page(page, page_width)

                # Extract images for this page
                extracted_images = ImageExtractor.extract_images_from_page(doc, page_num)

                # Fallback: if page is scanned and no embedded raster or OCR text was found,
                # render the page visual directly so content is preserved in Word
                if is_page_scanned and not extracted_images and not text_blocks:
                    pix = page.get_pixmap(dpi=150, alpha=False)
                    extracted_images.append(
                        ExtractedImage(
                            page_number=page_num,
                            image_bytes=pix.tobytes("png"),
                            format="png",
                            bbox=page.rect,
                            width=pix.width,
                            height=pix.height,
                        )
                    )

                # Get tables for this page
                extracted_tables = tables_by_page.get(page_num, [])

                # Stage 5: Reconstructing Layout
                page_flow = LayoutAnalyzer.assemble_page_flow(
                    text_blocks=text_blocks,
                    tables=extracted_tables,
                    images=extracted_images,
                    page_width=page_width,
                )

                # Add elements to Word document
                for element in page_flow:
                    if element.element_type == "heading":
                        docx_gen.add_heading(element.content)
                    elif element.element_type == "list_item":
                        docx_gen.add_list_item(element.content)
                    elif element.element_type == "paragraph":
                        docx_gen.add_paragraph(element.content)
                    elif element.element_type == "table":
                        docx_gen.add_table(element.content)
                    elif element.element_type == "image":
                        docx_gen.add_image(element.content)

                # Add page break if not last page
                if page_num < total_pages:
                    docx_gen.add_page_break()

            doc.close()

            # 4. Save reconstructed Word document
            self.store.update_job(
                job_id,
                stage=ConversionStage.RECONSTRUCTING,
                stage_message="Reconstructing Word document (.docx)...",
                progress=90,
            )

            docx_gen.save(str(output_path))

            # 5. Conversion Complete
            duration = round(time.time() - start_time, 2)
            out_size = output_path.stat().st_size if output_path.exists() else 0

            # Generate target docx filename
            base_name = os.path.splitext(original_filename)[0]
            docx_name = f"{base_name}.docx"

            conversion_res = ConversionResult(
                file_id=file_id,
                job_id=job_id,
                original_filename=original_filename,
                docx_filename=docx_name,
                download_url=f"/api/download/{file_id}",
                page_count=total_pages,
                is_scanned=analysis.is_scanned,
                ocr_used=ocr_was_used,
                extracted_elements=docx_gen.stats,
                duration_seconds=duration,
                file_size_bytes=out_size,
                completed_at=datetime.now(timezone.utc).isoformat() + "Z",
            )

            self.store.update_job(
                job_id,
                status=JobStatus.COMPLETED,
                stage=ConversionStage.COMPLETED,
                stage_message="Conversion complete",
                progress=100,
                result=conversion_res,
            )
            logger.info(f"Successfully converted {original_filename} in {duration}s")

        except PDFValidationError as pve:
            logger.warning(f"PDF Validation error for job {job_id}: {pve}")
            self.store.update_job(
                job_id,
                status=JobStatus.FAILED,
                stage=ConversionStage.FAILED,
                stage_message="Validation failed",
                error_message=pve.user_friendly_message,
                progress=0,
            )
        except Exception as e:
            logger.error(f"Unexpected error in conversion job {job_id}: {e}", exc_info=True)
            self.store.update_job(
                job_id,
                status=JobStatus.FAILED,
                stage=ConversionStage.FAILED,
                stage_message="Conversion error",
                error_message="Unable to convert this PDF. The document may be corrupted or contains unsupported structures.",
                progress=0,
            )


conversion_service = ConversionService()
