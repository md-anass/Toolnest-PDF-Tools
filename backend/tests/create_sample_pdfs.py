import io
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF

FIXTURES_DIR = Path(__file__).parent / "fixtures"
FIXTURES_DIR.mkdir(parents=True, exist_ok=True)


def create_normal_text_pdf() -> str:
    """Create a standard text PDF with headings, paragraphs, bold/italic, and bullet list."""
    path = FIXTURES_DIR / "normal_text.pdf"
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)  # Letter size

    # PyMuPDF insert_text
    page.insert_text((54, 72), "Quarterly Financial Analysis Report", fontsize=20, fontname="helv", color=(0.1, 0.15, 0.3))
    page.insert_text((54, 110), "Executive Summary", fontsize=15, fontname="helv", color=(0.15, 0.2, 0.35))
    page.insert_text(
        (54, 135),
        "During the third quarter, corporate revenue increased by 24% year-over-year. Operational efficiency\n"
        "gains were driven by automation and cloud workload consolidation across business units.",
        fontsize=11, fontname="helv"
    )

    page.insert_text((54, 185), "Key Accomplishments", fontsize=14, fontname="helv", color=(0.15, 0.2, 0.35))
    page.insert_text((54, 210), "• Expanded digital conversion infrastructure to 99.9% uptime SLA.", fontsize=11, fontname="helv")
    page.insert_text((54, 230), "• Reduced document processing latency by 45% for high-volume jobs.", fontsize=11, fontname="helv")
    page.insert_text((54, 250), "• Implemented enterprise-grade end-to-end encryption for all payloads.", fontsize=11, fontname="helv")

    page.insert_text((54, 290), "Market Outlook and Guidance", fontsize=14, fontname="helv", color=(0.15, 0.2, 0.35))
    page.insert_text(
        (54, 315),
        "We expect steady growth into the upcoming fiscal year. Customer adoption of automated file translation\n"
        "and document workflow tools continues to accelerate across enterprise accounts.",
        fontsize=11, fontname="helv"
    )

    doc.save(str(path))
    doc.close()
    return str(path)


def create_scanned_pdf() -> str:
    """Create a scanned-style PDF: rendered image of text with NO selectable text layer."""
    path = FIXTURES_DIR / "scanned_document.pdf"

    # Create high-contrast image using PIL
    img = Image.new("RGB", (1200, 1600), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Draw simulated scanned text onto the bitmap
    draw.text((100, 120), "OFFICIAL INVOICE AND DISPATCH NOTE", fill=(20, 20, 20))
    draw.text((100, 200), "Vendor: Global Document Solutions Inc.", fill=(40, 40, 40))
    draw.text((100, 260), "Invoice Number: INV-984210", fill=(40, 40, 40))
    draw.text((100, 320), "Status: Verified and Audited", fill=(40, 40, 40))
    draw.text((100, 400), "This page was produced by an optical flatbed scanner at 300 DPI.", fill=(50, 50, 50))
    draw.text((100, 460), "All text is contained purely in the raster image bitmap.", fill=(50, 50, 50))

    img_buffer = io.BytesIO()
    img.save(img_buffer, format="JPEG", quality=90)
    img_bytes = img_buffer.getvalue()

    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    # Insert image filling entire page
    page.insert_image(fitz.Rect(0, 0, 612, 792), stream=img_bytes)

    doc.save(str(path))
    doc.close()
    return str(path)


def create_image_rich_pdf() -> str:
    """Create a PDF with text and an embedded raster diagram/image."""
    path = FIXTURES_DIR / "image_rich.pdf"

    # Create a nice sample diagram image
    img = Image.new("RGB", (400, 200), color=(240, 248, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([20, 20, 380, 180], outline=(40, 100, 200), width=3)
    draw.ellipse([50, 50, 150, 150], fill=(70, 130, 240))
    draw.rectangle([200, 50, 350, 150], fill=(30, 180, 120))
    draw.text((60, 90), "Source PDF", fill=(255, 255, 255))
    draw.text((220, 90), "Target Word", fill=(255, 255, 255))

    img_buf = io.BytesIO()
    img.save(img_buf, format="PNG")
    img_bytes = img_buf.getvalue()

    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((54, 72), "Architecture Design Overview", fontsize=18, fontname="helv", color=(0.1, 0.2, 0.4))
    page.insert_text((54, 105), "The following diagram depicts the pipeline architecture and flow:", fontsize=11, fontname="helv")

    # Insert image in middle of page
    page.insert_image(fitz.Rect(100, 130, 512, 330), stream=img_bytes)

    page.insert_text((54, 360), "Figure 1: High-level architectural pipeline schema.", fontsize=10, fontname="helv", color=(0.4, 0.4, 0.4))
    page.insert_text((54, 390), "Each pipeline stage operates asynchronously with automated resource allocation.", fontsize=11, fontname="helv")

    doc.save(str(path))
    doc.close()
    return str(path)


def create_table_pdf() -> str:
    """Create a PDF containing structured tabular lines and data."""
    path = FIXTURES_DIR / "table_document.pdf"
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)

    page.insert_text((54, 72), "Product Inventory Schedule", fontsize=18, fontname="helv")
    page.insert_text((54, 100), "Detailed inventory log for hardware and storage assets:", fontsize=11, fontname="helv")

    # Draw table grid lines
    y_start = 130
    row_height = 25
    col_widths = [150, 120, 100, 134]
    x_start = 54
    headers = ["SKU Description", "Category", "Quantity", "Unit Price"]
    rows = [
        ["High-Speed NVMe Storage", "Hardware", "140", "$189.00"],
        ["Rackmount Server 2U", "Compute", "25", "$2,450.00"],
        ["Gigabit Switch 48-Port", "Networking", "12", "$620.00"],
        ["Redundant Power Unit", "Hardware", "50", "$145.00"],
    ]

    # Draw headers
    curr_x = x_start
    for i, h in enumerate(headers):
        page.insert_text((curr_x + 5, y_start + 18), h, fontsize=10, fontname="helv")
        curr_x += col_widths[i]

    # Draw data rows
    for r_idx, row in enumerate(rows):
        r_y = y_start + ((r_idx + 1) * row_height)
        curr_x = x_start
        for c_idx, val in enumerate(row):
            page.insert_text((curr_x + 5, r_y + 18), val, fontsize=10, fontname="helv")
            curr_x += col_widths[c_idx]

    # Draw horizontal table lines
    total_w = sum(col_widths)
    for r_i in range(len(rows) + 2):
        ly = y_start + (r_i * row_height)
        page.draw_line(fitz.Point(x_start, ly), fitz.Point(x_start + total_w, ly), color=(0.7, 0.7, 0.7), width=1)

    doc.save(str(path))
    doc.close()
    return str(path)


def create_multi_page_pdf() -> str:
    """Create a 3-page document."""
    path = FIXTURES_DIR / "multi_page.pdf"
    doc = fitz.open()

    for p in range(1, 4):
        page = doc.new_page(width=612, height=792)
        page.insert_text((54, 72), f"Comprehensive Operations Manual - Chapter {p}", fontsize=18, fontname="helv")
        page.insert_text((54, 110), f"Section {p}.1: Procedures and Guidelines", fontsize=14, fontname="helv")
        page.insert_text(
            (54, 140),
            f"This is page {p} of the multi-page manual. Standard operating policies require\n"
            f"periodic review and compliance certification across all production services.",
            fontsize=11, fontname="helv"
        )
        page.insert_text((54, 740), f"Page {p} of 3", fontsize=9, fontname="helv", color=(0.5, 0.5, 0.5))

    doc.save(str(path))
    doc.close()
    return str(path)


def create_corrupted_pdf() -> str:
    """Create a non-PDF file masquerading as a PDF."""
    path = FIXTURES_DIR / "corrupted.pdf"
    with open(path, "wb") as f:
        f.write(b"NOT A VALID PDF HEADER CORRUPTED FILE CONTENT RANDOM BYTES 1234567890")
    return str(path)


def create_password_protected_pdf() -> str:
    """Create a password-encrypted PDF."""
    path = FIXTURES_DIR / "password_protected.pdf"
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((54, 72), "Confidential Strategic Roadmap", fontsize=18, fontname="helv")
    page.insert_text((54, 110), "This document is confidential and password encrypted.", fontsize=11, fontname="helv")

    perm = int(
        fitz.PDF_PERM_ACCESSIBILITY
        | fitz.PDF_PERM_PRINT
        | fitz.PDF_PERM_COPY
        | fitz.PDF_PERM_ANNOTATE
    )
    doc.save(
        str(path),
        encryption=fitz.PDF_ENCRYPT_AES_256,
        user_pw="SecretPassword123",
        owner_pw="OwnerSecret456",
        permissions=perm,
    )
    doc.close()
    return str(path)


def generate_all_fixtures():
    create_normal_text_pdf()
    create_scanned_pdf()
    create_image_rich_pdf()
    create_table_pdf()
    create_multi_page_pdf()
    create_corrupted_pdf()
    create_password_protected_pdf()
    print("All test PDF fixtures generated successfully in:", FIXTURES_DIR)


if __name__ == "__main__":
    generate_all_fixtures()
