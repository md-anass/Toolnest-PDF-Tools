import logging
from typing import List, Tuple, Optional
import fitz  # PyMuPDF
import pdfplumber
from app.models.conversion import (
    PDFMetadata,
    PageAnalysis,
    DocumentAnalysis,
)

logger = logging.getLogger(__name__)

# Thresholds for scanned page detection
MIN_CHARS_FOR_TEXT_PAGE = 35  # If page has fewer characters than this
MIN_TEXT_DENSITY = 0.00015     # characters / (width * height in points)


class PDFAnalyzer:
    """Analyzes PDF structure, detecting text density, scanned pages, images, and tables."""

    @staticmethod
    def analyze_document(file_path: str) -> DocumentAnalysis:
        """Perform comprehensive analysis of a PDF document."""
        doc = fitz.open(file_path)
        try:
            page_count = doc.page_count
            if page_count == 0:
                raise ValueError("PDF document contains no pages.")

            # 1. Metadata
            meta = doc.metadata or {}
            pdf_metadata = PDFMetadata(
                title=meta.get("title") or None,
                author=meta.get("author") or None,
                subject=meta.get("subject") or None,
                creator=meta.get("creator") or None,
                producer=meta.get("producer") or None,
                creation_date=meta.get("creationDate") or None,
                mod_date=meta.get("modDate") or None,
            )

            pages_analysis: List[PageAnalysis] = []
            total_chars = 0
            total_words = 0
            total_images = 0
            total_tables = 0
            scanned_pages: List[int] = []
            selectable_pages: List[int] = []
            densities: List[float] = []

            # 2. Check tables with pdfplumber safely
            tables_per_page = {}
            try:
                with pdfplumber.open(file_path) as plum_pdf:
                    for idx, plum_page in enumerate(plum_pdf.pages):
                        found_tables = plum_page.extract_tables() or []
                        tables_per_page[idx + 1] = len(found_tables)
            except Exception as e:
                logger.warning(f"pdfplumber table extraction warning: {e}")
                # Fallback to 0 tables per page if pdfplumber encounters non-fatal issue
                tables_per_page = {p: 0 for p in range(1, page_count + 1)}

            # 3. Analyze each page with PyMuPDF
            for page_idx in range(page_count):
                page_num = page_idx + 1
                page = doc[page_idx]
                rect = page.rect
                page_area = max(rect.width * rect.height, 1.0)

                # Extract text
                text = page.get_text("text") or ""
                clean_text = text.strip()
                char_count = len(clean_text)
                words = clean_text.split()
                word_count = len(words)

                # Extract images
                image_list = page.get_images(full=True)
                image_count = len(image_list)

                # Calculate text density
                density = char_count / page_area
                densities.append(density)

                # Table count
                page_table_count = tables_per_page.get(page_num, 0)

                # Detect if page is scanned
                # A page is considered scanned if:
                # - Very low char count (< MIN_CHARS_FOR_TEXT_PAGE) AND has at least 1 image
                # - OR density < MIN_TEXT_DENSITY and char_count < 100
                is_scanned = False
                if char_count < MIN_CHARS_FOR_TEXT_PAGE:
                    # If there's an image, or page is virtually blank with no text, mark scanned
                    if image_count > 0:
                        is_scanned = True
                    elif char_count == 0:
                        # Page is blank or purely graphic
                        is_scanned = True
                elif density < MIN_TEXT_DENSITY and char_count < 60:
                    is_scanned = True

                has_selectable_text = char_count >= MIN_CHARS_FOR_TEXT_PAGE

                if is_scanned:
                    scanned_pages.append(page_num)
                else:
                    selectable_pages.append(page_num)

                total_chars += char_count
                total_words += word_count
                total_images += image_count
                total_tables += page_table_count

                pages_analysis.append(
                    PageAnalysis(
                        page_number=page_num,
                        char_count=char_count,
                        word_count=word_count,
                        image_count=image_count,
                        table_count=page_table_count,
                        is_scanned=is_scanned,
                        text_density=round(density, 6),
                        has_selectable_text=has_selectable_text,
                    )
                )

            avg_density = sum(densities) / len(densities) if densities else 0.0

            # Document is considered predominantly scanned if >50% of pages are scanned
            # or if the document has 0 selectable text and has images
            is_doc_scanned = len(scanned_pages) > 0 and (
                len(scanned_pages) >= (page_count / 2) or total_chars < (page_count * 20)
            )

            # OCR is recommended if any page is scanned
            ocr_recommended = len(scanned_pages) > 0

            return DocumentAnalysis(
                page_count=page_count,
                total_characters=total_chars,
                total_words=total_words,
                total_images=total_images,
                total_tables=total_tables,
                is_scanned=is_doc_scanned,
                scanned_pages=scanned_pages,
                selectable_pages=selectable_pages,
                ocr_recommended=ocr_recommended,
                average_text_density=round(avg_density, 6),
                metadata=pdf_metadata,
            )

        finally:
            doc.close()
