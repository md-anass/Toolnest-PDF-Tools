import io
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

import fitz
from PIL import Image, ImageSequence

from app.utils.file_validation import MAX_FILE_SIZE_BYTES


PDF_EXTENSIONS = {".pdf"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}
OFFICE_EXTENSIONS = {
    ".doc", ".docx", ".odt", ".rtf", ".ppt", ".pptx", ".odp",
    ".xls", ".xlsx", ".ods", ".csv",
}
SUPPORTED_EXTENSIONS = PDF_EXTENSIONS | IMAGE_EXTENSIONS | OFFICE_EXTENSIONS | {".txt"}
MAX_MERGE_FILES = 20


def _find_office_binary() -> str | None:
    configured_path = os.environ.get("LIBREOFFICE_PATH")
    local_path = Path(__file__).resolve().parents[2] / "tools" / "libreoffice" / "program" / "soffice.exe"
    for candidate in (configured_path, str(local_path)):
        if candidate and Path(candidate).is_file():
            return candidate
    return shutil.which("soffice") or shutil.which("libreoffice")


def _safe_stem(filename: str) -> str:
    stem = Path(filename).stem
    return re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._") or "document"


def _read_pdf(content: bytes) -> fitz.Document:
    document = fitz.open(stream=content, filetype="pdf")
    if document.is_encrypted and not document.authenticate(""):
        document.close()
        raise ValueError("Password-protected PDFs are not supported. Remove the password and try again.")
    if document.page_count < 1:
        document.close()
        raise ValueError("The PDF does not contain any pages.")
    return document


def _compress_pdf(content: bytes) -> bytes:
    document = _read_pdf(content)
    try:
        return document.tobytes(garbage=4, deflate=True, clean=True, deflate_images=True, deflate_fonts=True)
    finally:
        document.close()


def _merge_pdfs(files: list[tuple[str, bytes]]) -> bytes:
    merged = fitz.open()
    sources: list[fitz.Document] = []
    try:
        for _, content in files:
            source = _read_pdf(content)
            sources.append(source)
            merged.insert_pdf(source)
        return merged.tobytes(garbage=4, deflate=True)
    finally:
        merged.close()
        for source in sources:
            source.close()


def _split_pdf(filename: str, content: bytes) -> bytes:
    source = _read_pdf(content)
    archive_buffer = io.BytesIO()
    stem = _safe_stem(filename)
    try:
        with zipfile.ZipFile(archive_buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            for page_index in range(source.page_count):
                page_document = fitz.open()
                try:
                    page_document.insert_pdf(source, from_page=page_index, to_page=page_index)
                    archive.writestr(
                        f"{stem}_page_{page_index + 1}.pdf",
                        page_document.tobytes(garbage=4, deflate=True),
                    )
                finally:
                    page_document.close()
    finally:
        source.close()
    return archive_buffer.getvalue()


def _images_to_pdf(content: bytes) -> bytes:
    output = fitz.open()
    try:
        with Image.open(io.BytesIO(content)) as image:
            for frame in ImageSequence.Iterator(image):
                rgb_frame = frame.convert("RGB")
                page_width = max(1, rgb_frame.width * 72 / 150)
                page_height = max(1, rgb_frame.height * 72 / 150)
                page = output.new_page(width=page_width, height=page_height)
                image_buffer = io.BytesIO()
                rgb_frame.save(image_buffer, format="PNG")
                page.insert_image(page.rect, stream=image_buffer.getvalue())
        return output.tobytes(garbage=4, deflate=True)
    finally:
        output.close()


def _text_to_pdf(content: bytes) -> bytes:
    text = content.decode("utf-8-sig", errors="replace")
    output = fitz.open()
    page = output.new_page()
    cursor_y = 48
    for line in text.splitlines() or [""]:
        wrapped_lines = [line[index:index + 100] for index in range(0, max(1, len(line)), 100)]
        for wrapped_line in wrapped_lines:
            if cursor_y > 780:
                page = output.new_page()
                cursor_y = 48
            page.insert_text((48, cursor_y), wrapped_line, fontsize=10)
            cursor_y += 14
    try:
        return output.tobytes(garbage=4, deflate=True)
    finally:
        output.close()


def _office_to_pdf(filename: str, content: bytes) -> bytes:
    office_binary = _find_office_binary()
    if not office_binary:
        raise RuntimeError(
            "Office conversion requires LibreOffice. Install LibreOffice on the backend server and restart it."
        )

    suffix = Path(filename).suffix.lower()
    with tempfile.TemporaryDirectory(prefix="pdf_tool_") as temp_dir:
        input_path = Path(temp_dir) / f"source{suffix}"
        input_path.write_bytes(content)
        try:
            subprocess.run(
                [office_binary, "--headless", "--convert-to", "pdf", "--outdir", temp_dir, str(input_path)],
                check=True,
                capture_output=True,
                timeout=90,
            )
        except subprocess.TimeoutExpired as error:
            raise RuntimeError("Office conversion timed out. Try a smaller document.") from error
        except subprocess.CalledProcessError as error:
            raise ValueError("LibreOffice could not convert this file. Check that the document is valid.") from error

        output_path = Path(temp_dir) / "source.pdf"
        if not output_path.exists():
            raise ValueError("LibreOffice did not produce a PDF for this document.")
        return output_path.read_bytes()


def process_document_tool(operation: str, files: list[tuple[str, bytes]]) -> tuple[bytes, str, str]:
    if operation == "merge":
        if not 2 <= len(files) <= MAX_MERGE_FILES:
            raise ValueError(f"Choose between 2 and {MAX_MERGE_FILES} PDFs to merge.")
        if any(Path(filename).suffix.lower() not in PDF_EXTENSIONS for filename, _ in files):
            raise ValueError("Only PDF files can be merged.")
        content = _merge_pdfs(files)
        return content, "application/pdf", "merged_document.pdf"

    if len(files) != 1:
        raise ValueError("Choose exactly one file for this operation.")

    filename, content = files[0]
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError("This file type is not supported. Choose PDF, DOC/DOCX, PPT/PPTX, XLS/XLSX, ODF, RTF, CSV, TXT, or an image.")

    stem = _safe_stem(filename)
    if operation == "split":
        if extension not in PDF_EXTENSIONS:
            raise ValueError("Only PDF files can be split.")
        return _split_pdf(filename, content), "application/zip", f"{stem}_pages.zip"
    if operation == "compress":
        if extension not in PDF_EXTENSIONS:
            raise ValueError("Only PDF files can be compressed.")
        return _compress_pdf(content), "application/pdf", f"{stem}_compressed.pdf"
    if operation == "to-pdf":
        if extension in PDF_EXTENSIONS:
            _read_pdf(content).close()
            return content, "application/pdf", f"{stem}.pdf"
        if extension in IMAGE_EXTENSIONS:
            result = _images_to_pdf(content)
        elif extension == ".txt":
            result = _text_to_pdf(content)
        else:
            result = _office_to_pdf(filename, content)
        return result, "application/pdf", f"{stem}.pdf"

    raise ValueError("Unknown operation. Choose merge, split, compress, or to-pdf.")