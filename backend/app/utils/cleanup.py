import os
import time
import logging
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger(__name__)

# Base directory for temporary files (isolated from public web access)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
TMP_DIR = BASE_DIR / "tmp"
UPLOAD_DIR = TMP_DIR / "uploads"
OUTPUT_DIR = TMP_DIR / "outputs"

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Default retention time in seconds: 30 minutes
DEFAULT_FILE_TTL_SECONDS = 1800


def get_upload_path(file_id: str) -> Path:
    """Get the absolute path for an uploaded PDF file."""
    # Sanitize file_id to prevent directory traversal
    safe_id = os.path.basename(file_id)
    return UPLOAD_DIR / f"{safe_id}.pdf"


def get_output_path(file_id: str) -> Path:
    """Get the absolute path for a generated DOCX file."""
    safe_id = os.path.basename(file_id)
    return OUTPUT_DIR / f"{safe_id}.docx"


def remove_file_safely(file_path: Path) -> bool:
    """Safely remove a file if it exists."""
    try:
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Safely deleted temporary file: {file_path}")
            return True
    except Exception as e:
        logger.warning(f"Failed to delete {file_path}: {e}")
    return False


def delete_job_files(file_id: str) -> dict:
    """Delete all temporary files associated with a file_id / job_id."""
    upload_path = get_upload_path(file_id)
    output_path = get_output_path(file_id)

    deleted_upload = remove_file_safely(upload_path)
    deleted_output = remove_file_safely(output_path)

    return {
        "upload_deleted": deleted_upload,
        "output_deleted": deleted_output,
        "file_id": file_id,
    }


def clean_stale_files(max_age_seconds: int = DEFAULT_FILE_TTL_SECONDS) -> int:
    """Scan upload and output directories and delete files older than max_age_seconds."""
    now = time.time()
    deleted_count = 0

    for directory in [UPLOAD_DIR, OUTPUT_DIR]:
        if not directory.exists():
            continue
        for file_path in directory.iterdir():
            if file_path.is_file():
                try:
                    file_age = now - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        file_path.unlink()
                        deleted_count += 1
                        logger.info(f"Cleaned up stale file: {file_path.name} (age: {int(file_age)}s)")
                except Exception as e:
                    logger.warning(f"Error checking/deleting file {file_path}: {e}")

    return deleted_count
