import io
import zipfile

import fitz
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app

client = TestClient(app)


def make_pdf(page_count: int) -> bytes:
    document = fitz.open()
    for page_number in range(page_count):
        page = document.new_page()
        page.insert_text((72, 72), f"Page {page_number + 1}")
    content = document.tobytes()
    document.close()
    return content


def test_merge_split_and_compress_pdf():
    first_pdf = make_pdf(2)
    second_pdf = make_pdf(1)

    merge_response = client.post(
        "/api/tools/merge",
        files=[
            ("files", ("first.pdf", first_pdf, "application/pdf")),
            ("files", ("second.pdf", second_pdf, "application/pdf")),
        ],
    )
    assert merge_response.status_code == 200
    with fitz.open(stream=merge_response.content, filetype="pdf") as merged:
        assert merged.page_count == 3

    split_response = client.post(
        "/api/tools/split",
        files={"files": ("sample.pdf", first_pdf, "application/pdf")},
    )
    assert split_response.status_code == 200
    with zipfile.ZipFile(io.BytesIO(split_response.content)) as archive:
        assert archive.namelist() == ["sample_page_1.pdf", "sample_page_2.pdf"]
        assert all(name.endswith(".pdf") for name in archive.namelist())

    compress_response = client.post(
        "/api/tools/compress",
        files={"files": ("sample.pdf", first_pdf, "application/pdf")},
    )
    assert compress_response.status_code == 200
    with fitz.open(stream=compress_response.content, filetype="pdf") as compressed:
        assert compressed.page_count == 2


def test_convert_image_to_pdf():
    image_buffer = io.BytesIO()
    Image.new("RGB", (32, 24), "white").save(image_buffer, format="PNG")

    response = client.post(
        "/api/tools/to-pdf",
        files={"files": ("diagram.png", image_buffer.getvalue(), "image/png")},
    )

    assert response.status_code == 200
    assert 'filename="diagram.pdf"' in response.headers["content-disposition"]
    with fitz.open(stream=response.content, filetype="pdf") as document:
        assert document.page_count == 1


def test_office_conversion_reports_missing_libreoffice(monkeypatch):
    monkeypatch.setattr("app.services.document_tools.shutil.which", lambda _: None)

    response = client.post(
        "/api/tools/to-pdf",
        files={"files": ("report.docx", b"not a real docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )

    assert response.status_code == 503
    assert "LibreOffice" in response.json()["message"]


def test_merge_rejects_non_pdf_files():
    response = client.post(
        "/api/tools/merge",
        files=[
            ("files", ("first.pdf", make_pdf(1), "application/pdf")),
            ("files", ("notes.txt", b"not a PDF", "text/plain")),
        ],
    )

    assert response.status_code == 400
    assert "Only PDF files" in response.json()["message"]
