import os
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from app.utils.cleanup import get_output_path, get_upload_path, delete_job_files
from app.services.conversion_service import job_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["files"])


@router.get("/download/{file_id}")
async def download_docx(file_id: str):
    """Download the generated Word document (.docx)."""
    # Sanitize file_id to prevent path traversal
    safe_id = os.path.basename(file_id)
    output_path = get_output_path(safe_id)

    if not output_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The requested Word document was not found or has expired.",
        )

    # Determine original filename from job store if available
    download_filename = f"{safe_id}.docx"
    for j_id, j_data in list(job_store._jobs.items()):
        if j_data.get("file_id") == safe_id:
            res = j_data.get("result")
            if res and hasattr(res, "docx_filename"):
                download_filename = res.docx_filename
            elif res and isinstance(res, dict) and "docx_filename" in res:
                download_filename = res["docx_filename"]
            else:
                orig = j_data.get("original_filename", "document.pdf")
                base = os.path.splitext(orig)[0]
                download_filename = f"{base}.docx"
            break

    return FileResponse(
        path=str(output_path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=download_filename,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Content-Disposition": f'attachment; filename="{download_filename}"',
        },
    )


@router.delete("/files/{file_id}")
async def delete_temporary_files(file_id: str):
    """Explicitly delete uploaded and converted temporary files."""
    safe_id = os.path.basename(file_id)
    deletion_result = delete_job_files(safe_id)

    # Remove from job store if matching
    matching_jobs = [
        jid for jid, jdata in list(job_store._jobs.items())
        if jdata.get("file_id") == safe_id
    ]
    for jid in matching_jobs:
        job_store.delete_job(jid)

    return {
        "success": True,
        "message": "Temporary files removed securely from server.",
        "details": deletion_result,
    }
