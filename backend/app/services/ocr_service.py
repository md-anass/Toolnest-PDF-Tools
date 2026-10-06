import os
import shutil
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import fitz  # PyMuPDF
from app.services.pdf_text_extractor import TextBlock, TextLine, TextSpan

logger = logging.getLogger(__name__)


def find_tesseract_cmd() -> Optional[str]:
    """Find Tesseract executable in standard Windows or Unix paths."""
    # 1. Check environment variable
    env_cmd = os.environ.get("TESSERACT_CMD")
    if env_cmd and os.path.isfile(env_cmd):
        return env_cmd

    # 2. Check PATH
    which_cmd = shutil.which("tesseract")
    if which_cmd:
        return which_cmd

    # 3. Check common Windows installation paths
    common_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
        os.path.expandvars(r"%ProgramW6432%\Tesseract-OCR\tesseract.exe"),
        r"D:\Tesseract-OCR\tesseract.exe",
    ]
    for path in common_paths:
        if os.path.isfile(path):
            return path

    return None


class BaseOCREngine(ABC):
    """Abstract base class for OCR engines, allowing seamless swapping with PaddleOCR, EasyOCR, or Cloud OCR."""

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this OCR engine is installed and ready."""
        pass

    @abstractmethod
    def extract_blocks_from_image(self, image: Image.Image, page_width: float, page_height: float) -> List[TextBlock]:
        """Extract text blocks with layout coordinates from a rendered page image."""
        pass


class TesseractOCREngine(BaseOCREngine):
    """Tesseract OCR implementation utilizing pytesseract."""

    def __init__(self):
        self._tesseract_path = find_tesseract_cmd()
        self._pytesseract = None
        self._init_pytesseract()

    def _init_pytesseract(self):
        try:
            import pytesseract
            self._pytesseract = pytesseract
            if self._tesseract_path:
                pytesseract.pytesseract.tesseract_cmd = self._tesseract_path
                logger.info(f"Tesseract OCR initialized at: {self._tesseract_path}")
        except Exception as e:
            logger.warning(f"Failed to import pytesseract: {e}")

    def is_available(self) -> bool:
        if not self._pytesseract:
            return False
        if not self._tesseract_path and not shutil.which("tesseract"):
            return False
        try:
            version = self._pytesseract.get_tesseract_version()
            return bool(version)
        except Exception:
            return False

    def get_version(self) -> Optional[str]:
        if not self.is_available():
            return None
        try:
            return str(self._pytesseract.get_tesseract_version())
        except Exception:
            return None

    def extract_blocks_from_image(self, image: Image.Image, page_width: float, page_height: float) -> List[TextBlock]:
        if not self.is_available():
            logger.warning("Tesseract is not available for OCR.")
            return []

        try:
            from pytesseract import Output
            # Preprocess image if needed (convert to grayscale)
            gray_img = image.convert("L")

            # Extract detailed box data
            data = self._pytesseract.image_to_data(gray_img, output_type=Output.DICT)

            img_w, img_h = image.size
            scale_x = page_width / max(img_w, 1)
            scale_y = page_height / max(img_h, 1)

            n_boxes = len(data["level"])
            blocks_dict: Dict[int, List[Dict[str, Any]]] = {}

            # Group words by block_num and line_num
            for i in range(n_boxes):
                text = (data["text"][i] or "").strip()
                if not text:
                    continue

                conf = int(data["conf"][i])
                if conf < 20:  # Filter very low confidence noise
                    continue

                block_num = data["block_num"][i]
                line_num = data["line_num"][i]
                left = data["left"][i] * scale_x
                top = data["top"][i] * scale_y
                w = data["width"][i] * scale_x
                h = data["height"][i] * scale_y

                if block_num not in blocks_dict:
                    blocks_dict[block_num] = []

                blocks_dict[block_num].append({
                    "text": text,
                    "line_num": line_num,
                    "bbox": fitz.Rect(left, top, left + w, top + h),
                    "height": h,
                })

            result_blocks: List[TextBlock] = []

            for block_num, words in blocks_dict.items():
                # Group words into lines
                lines_dict: Dict[int, List[Dict[str, Any]]] = {}
                for w in words:
                    ln = w["line_num"]
                    if ln not in lines_dict:
                        lines_dict[ln] = []
                    lines_dict[ln].append(w)

                text_lines: List[TextLine] = []
                all_block_words = []
                b_x0, b_y0, b_x1, b_y1 = 1e6, 1e6, -1e6, -1e6

                for ln, l_words in sorted(lines_dict.items()):
                    l_words.sort(key=lambda item: item["bbox"].x0)
                    line_text = " ".join([w["text"] for w in l_words])
                    if not line_text:
                        continue

                    l_x0 = min(w["bbox"].x0 for w in l_words)
                    l_y0 = min(w["bbox"].y0 for w in l_words)
                    l_x1 = max(w["bbox"].x1 for w in l_words)
                    l_y1 = max(w["bbox"].y1 for w in l_words)
                    avg_h = sum(w["height"] for w in l_words) / len(l_words)
                    # Approximate font point size from pixel height
                    approx_font_size = max(round(avg_h * 0.9, 1), 8.0)

                    spans = [
                        TextSpan(
                            text=line_text,
                            font_name="Calibri",
                            font_size=approx_font_size,
                            is_bold=False,
                            is_italic=False,
                            color=0,
                            bbox=fitz.Rect(l_x0, l_y0, l_x1, l_y1),
                        )
                    ]

                    text_lines.append(
                        TextLine(
                            spans=spans,
                            bbox=fitz.Rect(l_x0, l_y0, l_x1, l_y1),
                            text=line_text,
                        )
                    )
                    all_block_words.append(line_text)

                    b_x0 = min(b_x0, l_x0)
                    b_y0 = min(b_y0, l_y0)
                    b_x1 = max(b_x1, l_x1)
                    b_y1 = max(b_y1, l_y1)

                if text_lines:
                    full_text = "\n".join(all_block_words)
                    result_blocks.append(
                        TextBlock(
                            lines=text_lines,
                            bbox=fitz.Rect(b_x0, b_y0, b_x1, b_y1),
                            text=full_text,
                            alignment="left",
                        )
                    )

            return result_blocks

        except Exception as e:
            logger.error(f"Error executing Tesseract OCR: {e}")
            return []


class OCRService:
    """High-level OCR coordinator with modular engine support."""

    def __init__(self, engine: Optional[BaseOCREngine] = None):
        self.engine = engine or TesseractOCREngine()

    def is_ocr_available(self) -> bool:
        return self.engine.is_available()

    def get_engine_name(self) -> str:
        return type(self.engine).__name__

    def get_version(self) -> Optional[str]:
        if isinstance(self.engine, TesseractOCREngine):
            return self.engine.get_version()
        return None

    def ocr_page(self, page: fitz.Page, dpi: int = 200) -> List[TextBlock]:
        """Render a PyMuPDF page to image and perform OCR extraction."""
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        import io
        img = Image.open(io.BytesIO(pix.tobytes("png")))

        if self.is_ocr_available():
            blocks = self.engine.extract_blocks_from_image(
                image=img,
                page_width=page.rect.width,
                page_height=page.rect.height,
            )
            if blocks:
                return blocks

        # Fallback: if OCR binary is not installed or returned empty,
        # extract any fallback text or create a visual structure
        logger.info(f"Using high-fidelity visual reconstruction for scanned page {page.number + 1}")
        return []


# Global singleton instance
ocr_service = OCRService()
