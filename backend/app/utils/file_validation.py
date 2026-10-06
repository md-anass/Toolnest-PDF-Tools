import os
import re
from typing import Tuple, Optional
import fitz  # PyMuPDF

# Max file size: 50 MB
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024
MIN_FILE_SIZE_BYTES = 64  # Minimal valid PDF size


class PDFValidationError(Exception):
    """Custom exception for PDF validation errors."""
    def __init__(self, message: str, user_friendly_message: str):
        super().__init__(message)
        self.user_friendly_message = user_friendly_message


def sanitize_filename(filename: str) -> str:
    """Sanitize user-provided filename to prevent path traversal and shell exploits."""
    if not filename:
        return "document.pdf"
    # Extract only the base name (no directories)
    base = os.path.basename(filename.replace("\\", "/"))
    # Remove null bytes and non-printable characters
    clean = re.sub(r'[\x00-\x1f\x7f]', '', base)
    # Strip dangerous characters
    clean = re.sub(r'[^\w\s\.-]', '_', clean).strip()
    if not clean:
        clean = "document.pdf"
    if not clean.lower().endswith(".pdf"):
        clean += ".pdf"
    return clean


def validate_pdf_bytes(content: bytes, original_filename: str = "") -> None:
    """Validate PDF binary content before saving or processing."""
    # 1. Size check
    size = len(content)
    if size < MIN_FILE_SIZE_BYTES:
        raise PDFValidationError(
            f"File too small ({size} bytes)",
            "The uploaded file is empty or too small to be a valid PDF document."
        )

    if size > MAX_FILE_SIZE_BYTES:
        max_mb = MAX_FILE_SIZE_BYTES // (1024 * 1024)
        raise PDFValidationError(
            f"File exceeds maximum allowed size ({size} > {MAX_FILE_SIZE_BYTES})",
            f"The file exceeds the maximum allowed size of {max_mb}MB."
        )

    # 2. Magic byte verification (%PDF-)
    # Look for %PDF- in the first 1024 bytes (some PDFs have leading BOM or whitespace)
    header_chunk = content[:1024]
    pdf_header_index = header_chunk.find(b"%PDF-")
    if pdf_header_index == -1:
        raise PDFValidationError(
            "Missing %PDF- magic bytes header",
            "The uploaded file is not a valid PDF document format."
        )

    # 3. Structure check with PyMuPDF
    try:
        doc = fitz.open(stream=content, filetype="pdf")
    except Exception as e:
        raise PDFValidationError(
            f"Failed to open PDF with PyMuPDF: {str(e)}",
            "Unable to read this PDF. The document may be corrupted or malformed."
        )

    try:
        # Check password protection / encryption
        if doc.is_encrypted:
            # Try empty password
            auth_success = doc.authenticate("")
            if not auth_success:
                raise PDFValidationError(
                    "PDF is password-protected and encrypted",
                    "This PDF is password-protected. Please remove the password before converting."
                )

        # Check page count
        if doc.page_count < 1:
            raise PDFValidationError(
                "PDF has 0 pages",
                "The PDF document does not contain any pages."
            )

    finally:
        doc.close()


def validate_pdf_file_path(file_path: str) -> None:
    """Validate an existing PDF file on disk."""
    if not os.path.exists(file_path):
        raise PDFValidationError("File does not exist", "The requested file could not be found.")

    size = os.path.getsize(file_path)
    if size > MAX_FILE_SIZE_BYTES:
        max_mb = MAX_FILE_SIZE_BYTES // (1024 * 1024)
        raise PDFValidationError(
            "File exceeds maximum size",
            f"The file exceeds the maximum allowed size of {max_mb}MB."
        )

    try:
        doc = fitz.open(file_path)
        if doc.is_encrypted and not doc.authenticate(""):
            raise PDFValidationError(
                "PDF is password protected",
                "This PDF is password-protected. Please remove the password before converting."
            )
        if doc.page_count < 1:
            raise PDFValidationError("PDF has 0 pages", "The PDF document contains no pages.")
        doc.close()
    except PDFValidationError:
        raise
    except Exception as e:
        raise PDFValidationError(
            f"PyMuPDF error opening file: {str(e)}",
            "Unable to convert this PDF. The document may be corrupted or password-protected."
        )
