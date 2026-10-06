import logging
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from starlette.concurrency import run_in_threadpool

from app.services.document_tools import MAX_MERGE_FILES, SUPPORTED_EXTENSIONS, process_document_tool
from app.utils.file_validation import MAX_FILE_SIZE_BYTES

logger = logging.getLogger(__name__)
router = APIRouter(prefix="", tags=["document tools"])
MAX_TOTAL_UPLOAD_BYTES = MAX_FILE_SIZE_BYTES * 2


@router.post("/tools/{operation}")
async def run_document_tool(operation: str, files: list[UploadFile] = File(...)):
    if operation not in {"merge", "split", "compress", "to-pdf"}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown document operation.")
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Choose at least one file.")
    if len(files) > MAX_MERGE_FILES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Choose no more than {MAX_MERGE_FILES} files.")

    upload_data: list[tuple[str, bytes]] = []
    total_size = 0
    for upload in files:
        filename = Path(upload.filename or "document").name
        extension = Path(filename).suffix.lower()
        if extension not in SUPPORTED_EXTENSIONS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This file type is not supported.")
        content = await upload.read(MAX_FILE_SIZE_BYTES + 1)
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Each file must be 50 MB or smaller.")
        total_size += len(content)
        if total_size > MAX_TOTAL_UPLOAD_BYTES:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="The total upload must be 100 MB or smaller.")
        upload_data.append((filename, content))

    try:
        content, media_type, download_name = await run_in_threadpool(
            process_document_tool, operation, upload_data
        )
    except RuntimeError as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    except Exception as error:
        logger.warning("Document tool %s failed: %s", operation, error)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to process this file. It may be corrupted or password-protected.") from error

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{download_name}"'},
    )