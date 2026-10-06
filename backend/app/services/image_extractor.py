import io
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from PIL import Image
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

# Minimum pixel dimensions for meaningful image content
MIN_IMAGE_WIDTH = 20
MIN_IMAGE_HEIGHT = 20
MIN_IMAGE_BYTES = 250


@dataclass
class ExtractedImage:
    page_number: int
    image_bytes: bytes
    format: str  # "png", "jpeg", etc.
    bbox: fitz.Rect  # Bounding box on the page
    width: int
    height: int
    dpi: int = 150


class ImageExtractor:
    """Extracts and prepares images from PDF pages with page coordinates."""

    @staticmethod
    def extract_images_from_page(doc: fitz.Document, page_number: int) -> List[ExtractedImage]:
        """Extract all valid content images from a specific 1-indexed page."""
        extracted: List[ExtractedImage] = []
        page_idx = page_number - 1
        if page_idx < 0 or page_idx >= doc.page_count:
            return extracted

        page = doc[page_idx]
        image_list = page.get_images(full=True)
        seen_xrefs = set()

        for img_info in image_list:
            xref = img_info[0]
            if xref in seen_xrefs:
                continue
            seen_xrefs.add(xref)

            try:
                base_image = doc.extract_image(xref)
                if not base_image:
                    continue

                image_bytes = base_image.get("image")
                ext = base_image.get("ext", "png").lower()
                width = base_image.get("width", 0)
                height = base_image.get("height", 0)

                # Skip tiny icons / tracking pixels
                if len(image_bytes) < MIN_IMAGE_BYTES:
                    continue
                if width < MIN_IMAGE_WIDTH or height < MIN_IMAGE_HEIGHT:
                    continue

                # Locate the image bbox on the page
                # page.get_image_rects(xref) returns rectangles where this image is placed
                rects = page.get_image_rects(xref)
                if rects:
                    for rect in rects:
                        extracted.append(
                            ExtractedImage(
                                page_number=page_number,
                                image_bytes=image_bytes,
                                format=ext,
                                bbox=rect,
                                width=width,
                                height=height,
                            )
                        )
                else:
                    # If rect not directly bound, assign full page or estimated center
                    default_rect = fitz.Rect(72, 72, page.rect.width - 72, page.rect.height - 72)
                    extracted.append(
                        ExtractedImage(
                            page_number=page_number,
                            image_bytes=image_bytes,
                            format=ext,
                            bbox=default_rect,
                            width=width,
                            height=height,
                        )
                    )

            except Exception as e:
                logger.warning(f"Error extracting image xref {xref} on page {page_number}: {e}")

        # Sort images by vertical position (y0)
        extracted.sort(key=lambda img: (img.bbox.y0, img.bbox.x0))
        return extracted
