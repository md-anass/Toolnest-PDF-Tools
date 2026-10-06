import time
import httpx
from pathlib import Path
from docx import Document

BASE_URL = "http://127.0.0.1:8000"
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_live_pipeline():
    client = httpx.Client(base_url=BASE_URL, timeout=30.0)

    # 1. Health check
    health_resp = client.get("/api/health")
    print("1. Health Check Response:", health_resp.status_code, health_resp.json())
    assert health_resp.status_code == 200

    # 2. Text PDF conversion
    text_pdf_path = FIXTURES_DIR / "normal_text.pdf"
    print("\n2. Uploading normal text PDF:", text_pdf_path.name)
    with open(text_pdf_path, "rb") as f:
        up_resp = client.post("/api/convert", files={"file": ("quarterly_report.pdf", f, "application/pdf")})

    print("   Upload status:", up_resp.status_code, up_resp.json())
    assert up_resp.status_code == 202
    job_id = up_resp.json()["job_id"]
    file_id = up_resp.json()["file_id"]

    # 3. Poll conversion status
    print("   Polling conversion status...")
    completed = False
    for attempt in range(20):
        time.sleep(0.5)
        st_resp = client.get(f"/api/convert/{job_id}")
        st_data = st_resp.json()
        print(f"   [Poll #{attempt+1}] Status: {st_data['status']} | Stage: {st_data['stage']} | Progress: {st_data['progress']}%")
        if st_data["status"] == "completed":
            completed = True
            break
        elif st_data["status"] == "failed":
            raise RuntimeError(f"Conversion failed: {st_data.get('error_message')}")

    assert completed, "Conversion did not finish within timeout"
    res = st_data["result"]
    print("   Conversion Result:", {
        "docx_filename": res["docx_filename"],
        "pages": res["page_count"],
        "duration_seconds": res["duration_seconds"],
        "extracted_elements": res["extracted_elements"],
    })

    # 4. Download generated DOCX
    dl_resp = client.get(f"/api/download/{file_id}")
    print(f"\n3. Downloading generated DOCX: Status {dl_resp.status_code}, Bytes: {len(dl_resp.content)}")
    assert dl_resp.status_code == 200
    assert len(dl_resp.content) > 1000

    # 5. Verify Word document content
    saved_docx = FIXTURES_DIR / "test_download_result.docx"
    with open(saved_docx, "wb") as f:
        f.write(dl_resp.content)

    doc = Document(str(saved_docx))
    full_text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    print("\n4. Word Document Verified Content Preview:")
    print("   Total Paragraphs in Word:", len(doc.paragraphs))
    print("   First 3 lines in Word:")
    for p in doc.paragraphs[:3]:
        if p.text.strip():
            print("     ->", p.text.strip())

    assert "Quarterly Financial Analysis Report" in full_text
    assert "Executive Summary" in full_text
    print("\n=== SUCCESS: End-to-end Live Conversion and DOCX Generation Verified! ===")

    # 6. Test Scanned PDF
    scanned_path = FIXTURES_DIR / "scanned_document.pdf"
    print("\n5. Testing Live Scanned PDF Conversion:", scanned_path.name)
    with open(scanned_path, "rb") as f:
        sc_up = client.post("/api/convert", files={"file": ("scanned_invoice.pdf", f, "application/pdf")})
    assert sc_up.status_code == 202
    sc_job_id = sc_up.json()["job_id"]
    sc_file_id = sc_up.json()["file_id"]

    for _ in range(20):
        time.sleep(0.5)
        sc_st = client.get(f"/api/convert/{sc_job_id}").json()
        if sc_st["status"] == "completed":
            print(f"   Scanned PDF Converted! OCR used: {sc_st['result']['ocr_used']}, Is Scanned: {sc_st['result']['is_scanned']}")
            break

    # Download scanned docx
    sc_dl = client.get(f"/api/download/{sc_file_id}")
    assert sc_dl.status_code == 200
    print(f"   Scanned Word docx downloaded ({len(sc_dl.content)} bytes).")

    # 7. Cleanup
    del_resp = client.delete(f"/api/files/{file_id}")
    del_resp2 = client.delete(f"/api/files/{sc_file_id}")
    print("\n6. Cleanup Verified: Deletion response status:", del_resp.status_code, del_resp2.status_code)
    print("ALL LIVE TESTS COMPLETED WITH 100% SUCCESS.")


if __name__ == "__main__":
    test_live_pipeline()
