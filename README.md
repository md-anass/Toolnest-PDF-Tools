# Toolnest — PDF and Document Tools

Toolnest is a document utility web application that converts PDFs to editable Word documents, merges and splits PDFs, compresses files, and converts supported documents and images to PDF.

Toolnest includes automatic scanned document detection and OCR fallback, with temporary-file cleanup for processed documents.

---

## 🌟 Key Highlights & Capabilities

- **High-Fidelity DOCX Reconstruction**: Emits authentic Microsoft Word `.docx` documents containing native paragraph runs, headings (H1–H3), styled tables, and embedded high-resolution graphics.
- **Intelligent Pre-Analysis**: Inspects character density, page layout, image coverage, and text selectability per page before conversion.
- **Selective OCR Fallback**: Runs OCR only when pages contain little or no extractable digital text, conserving resources while ensuring scanned documents are transcribed accurately.
- **Real-Time Asynchronous Processing**: Non-blocking background worker pipeline with 6 distinct progress stages and live progress percentages.
- **Strict Ephemeral Privacy & Automatic Purge**: Uploaded files and generated `.docx` outputs are isolated outside public web directories and automatically purged within 30 minutes. Users can also trigger immediate server file deletion after download.
- **Robust Security Validation**: Verifies magic bytes (`%PDF-`), file sizes, extension integrity, and catches password encryption and corrupted files with human-friendly error messages.
- **PDF Utilities and Document Conversion**: Merge multiple PDFs, split pages into a ZIP, compress PDFs, and convert DOC/DOCX, PPT/PPTX, XLS/XLSX, OpenDocument, RTF, CSV, TXT, and common images to PDF.

---

## 🏗️ Architecture & Technology Stack

### Frontend
- **Framework**: Next.js 16 (App Router with Turbopack)
- **Language**: TypeScript 5
- **Styling**: Tailwind CSS v4 with custom color tokens and glassmorphism utilities
- **Icons**: Lucide React
- **Architecture**: Modular component tree (`PDFUploader`, `FilePreview`, `ConversionProgress`, `ConversionResult`, `DownloadButton`, `ErrorMessage`, `HowItWorks`, `FeatureCard`, `FAQ`, `Header`, `Footer`)

### Backend
- **Framework**: FastAPI (Python 3.13)
- **Server**: Uvicorn (ASGI) with lifespan background workers
- **PDF Extraction**: PyMuPDF (`pymupdf`) & `pdfplumber`
- **OCR Engine**: Modular `BaseOCREngine` supporting Tesseract OCR (`pytesseract`) with high-resolution visual fallback
- **Word Reconstruction**: `python-docx`
- **Image Processing**: Pillow (`PIL`)
- **Office Rendering**: LibreOffice is required on the backend host to convert Office and OpenDocument files to PDF.
- **Testing**: `pytest`, `httpx`

---

## 📁 Repository Structure

```
PDF Tool/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── convert.py           # Upload, status polling, pre-analysis
│   │   │   ├── files.py             # DOCX download & immediate deletion
│   │   │   └── health.py            # Service health & OCR readiness
│   │   ├── models/
│   │   │   └── conversion.py        # Pydantic schemas for jobs & metrics
│   │   ├── services/
│   │   │   ├── pdf_analyzer.py      # Page count, density, scan detection
│   │   │   ├── pdf_text_extractor.py# Rich text, spans, fonts, styles
│   │   │   ├── ocr_service.py       # Tesseract OCR engine & modular interface
│   │   │   ├── image_extractor.py   # Embedded image extraction & positioning
│   │   │   ├── layout_analyzer.py   # Heading classification & flow assembly
│   │   │   ├── docx_generator.py    # Native .docx reconstruction
│   │   │   └── conversion_service.py# Asynchronous job state manager
│   │   ├── utils/
│   │   │   ├── file_validation.py   # Magic bytes, size, encryption checks
│   │   │   └── cleanup.py           # Temporary storage & automatic purge
│   │   └── main.py                  # FastAPI app entry point & lifespan
│   ├── tests/
│   │   ├── create_sample_pdfs.py    # Programmatic test PDF fixture generator
│   │   ├── test_conversion.py       # Unit & integration test suite (10 tests)
│   │   ├── test_live_server.py      # End-to-end live server validation script
│   │   └── fixtures/                # Generated sample PDF fixtures
│   ├── requirements.txt
│   └── pytest.ini
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── globals.css          # Tailwind CSS styles & design tokens
│   │   │   ├── layout.tsx           # SEO metadata & responsive viewport
│   │   │   └── page.tsx             # Interactive landing & conversion page
│   │   ├── components/              # Modular UI components
│   │   ├── lib/
│   │   │   └── api.ts               # Client API library with progress tracking
│   │   └── types/
│   │       └── conversion.ts        # TypeScript interfaces & stage enums
│   ├── package.json
│   ├── tsconfig.json
│   └── next.config.ts               # API proxy rewrites
└── README.md
```

---

## 🚀 Setup & Installation Instructions

### 1. Prerequisites
- **Python**: Version 3.10 to 3.13 (64-bit recommended)
- **Node.js**: Version 18.x to 22.x or later
- **npm**: Version 9.x or later

---

### 2. Backend Setup

1. Open a terminal in the project root:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - **Windows (PowerShell)**:
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - **Windows (cmd)**:
     ```cmd
     venv\Scripts\activate.bat
     ```
   - **macOS / Linux**:
     ```bash
     source venv/bin/activate
     ```

4. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. (Optional) Configure Tesseract OCR:
   - If Tesseract is installed, set the environment variable:
     ```bash
     export TESSERACT_CMD="C:/Program Files/Tesseract-OCR/tesseract.exe"
     ```
   - If Tesseract is not installed, Toolnest will gracefully apply high-fidelity visual reconstruction for scanned pages so no content is lost.

6. (Required for office-to-PDF conversions) Install LibreOffice on the backend host and ensure `soffice` (or `libreoffice`) is available on `PATH`. PDF, image, and text conversion do not require LibreOffice.

7. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   The backend API will be available at `http://127.0.0.1:8000`. Swagger documentation is available at `http://127.0.0.1:8000/docs`.

---

### 3. Frontend Setup

1. Open a second terminal in the frontend directory:
   ```bash
   cd frontend
   ```

2. Install frontend dependencies:
   ```bash
   npm install
   ```

3. Start the Next.js development server:
   ```bash
   npm run dev
   ```
   The frontend application will be accessible at `http://localhost:3000` (or `http://localhost:3001` if port 3000 is occupied).

---

## 🧪 Running Tests

### 1. Run Backend Unit & Integration Tests (pytest)
```bash
cd backend
.\venv\Scripts\pytest tests/test_conversion.py -v
```
All 10 test scenarios will execute:
- Health check
- Corrupted PDF rejection
- Password-protected PDF rejection
- Normal text analysis
- Scanned PDF analysis
- End-to-end digital text conversion
- Multi-page document conversion (3 pages)
- Scanned document conversion
- Image-rich PDF conversion
- Table reconstruction

### 2. Run Live Server End-to-End Validation
While the FastAPI server is running on port 8000:
```bash
python backend/tests/test_live_server.py
```
This script uploads a real PDF, polls progress through all 6 states, downloads the generated `.docx`, parses the document using `python-docx` to verify extracted text and paragraphs, converts a scanned PDF, and tests server cleanup.

---

## 📡 API Reference

| Method | Endpoint | Description | Status Code |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | Service status, version, and OCR engine readiness | `200 OK` |
| `POST` | `/api/analyze` | Multipart upload for fast pre-analysis (page count, density) | `200 OK` |
| `POST` | `/api/convert` | Upload PDF and start background conversion job | `202 Accepted` |
| `GET` | `/api/convert/{job_id}` | Poll conversion progress, stage, and result details | `200 OK` |
| `GET` | `/api/download/{file_id}` | Stream generated `.docx` file as an attachment | `200 OK` |
| `DELETE` | `/api/files/{file_id}` | Immediately delete uploaded and output temporary files | `200 OK` |
| `POST` | `/api/tools/merge` | Merge 2 to 20 uploaded PDF files | `200 OK` |
| `POST` | `/api/tools/split` | Split a PDF into per-page PDFs in a ZIP | `200 OK` |
| `POST` | `/api/tools/compress` | Rewrite a PDF with stream and object cleanup | `200 OK` |
| `POST` | `/api/tools/to-pdf` | Convert supported office, image, text, and PDF files to PDF | `200 OK` |

---

## 🔒 Security & Privacy Architecture

1. **Untrusted File Quarantine**: All incoming PDF files are validated for header signatures (`%PDF-`) before saving.
2. **Path Traversal Protection**: Filenames provided by users are strictly sanitized; disk paths use random UUID identifiers.
3. **No Code Execution**: Uploaded files are strictly treated as passive binary documents; no scripts or macros are executed.
4. **Lifecycle Auto-Purge**: A scheduled background thread sweeps temporary storage every 10 minutes, pruning any artifacts older than 30 minutes.
5. **Human-Friendly Error Handling**: Exceptions (e.g. encrypted or malformed PDFs) are sanitized to prevent internal path leaks or stack traces from reaching clients.

---

## 📄 License

MIT License. Designed and built with original SaaS branding and high-fidelity document parsing.
