import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
import fitz
from app.services.pdf_text_extractor import TextBlock, TextLine, TextSpan
from app.services.image_extractor import ExtractedImage

logger = logging.getLogger(__name__)


@dataclass
class ExtractedTable:
    page_number: int
    data: List[List[Optional[str]]]  # Rows and cell texts
    bbox: fitz.Rect
    num_rows: int
    num_cols: int


@dataclass
class PageLayoutElement:
    element_type: str  # "heading", "paragraph", "table", "image", "list_item"
    content: Any       # TextBlock, ExtractedTable, or ExtractedImage
    y0: float
    x0: float


class LayoutAnalyzer:
    """Classifies document elements, heading hierarchies, lists, reading order, and layouts."""

    @staticmethod
    def calculate_body_font_size(blocks: List[TextBlock]) -> float:
        """Find the median/predominant font size in text blocks to identify body text."""
        font_sizes = []
        for b in blocks:
            for line in b.lines:
                for span in line.spans:
                    # Weight by text length
                    weight = max(len(span.text.strip()), 1)
                    font_sizes.extend([span.font_size] * min(weight, 50))

        if not font_sizes:
            return 11.0

        font_sizes.sort()
        median_size = font_sizes[len(font_sizes) // 2]
        return max(median_size, 8.0)

    @classmethod
    def classify_headings_and_styles(cls, blocks: List[TextBlock], body_font_size: float) -> None:
        """Assign heading levels and formatting to text blocks in place."""
        for b in blocks:
            # Check maximum font size in the block
            max_size = 0.0
            is_any_bold = False

            for line in b.lines:
                for span in line.spans:
                    if span.font_size > max_size:
                        max_size = span.font_size
                    if span.is_bold:
                        is_any_bold = True

            clean_text = b.text.strip()
            # Headings are generally short (< 150 chars, 1-2 lines)
            is_short = len(clean_text) < 150 and len(b.lines) <= 3

            if is_short and not b.is_list_item:
                if max_size >= (body_font_size * 1.5) or (is_any_bold and max_size >= (body_font_size * 1.35)):
                    b.is_heading = True
                    b.heading_level = 1
                elif max_size >= (body_font_size * 1.25) or (is_any_bold and max_size >= (body_font_size * 1.15)):
                    b.is_heading = True
                    b.heading_level = 2
                elif (is_any_bold and max_size >= body_font_size) or max_size >= (body_font_size * 1.1):
                    b.is_heading = True
                    b.heading_level = 3

    @staticmethod
    def detect_multi_column_order(blocks: List[TextBlock], page_width: float) -> List[TextBlock]:
        """Detect two-column layout and sort blocks in reading order (col 1 top-to-bottom, then col 2)."""
        if len(blocks) < 4:
            # Simple single column sort by y0
            return sorted(blocks, key=lambda b: (b.bbox.y0, b.bbox.x0))

        midpoint = page_width / 2.0
        col1_blocks = []
        col2_blocks = []
        spanning_blocks = []

        for b in blocks:
            if b.bbox.x1 <= (midpoint + 20):
                col1_blocks.append(b)
            elif b.bbox.x0 >= (midpoint - 20):
                col2_blocks.append(b)
            else:
                spanning_blocks.append(b)

        # Multi-column exists if substantial blocks on both sides and few spanning blocks
        is_multi_column = (
            len(col1_blocks) >= 2
            and len(col2_blocks) >= 2
            and len(spanning_blocks) <= (len(blocks) * 0.3)
        )

        if not is_multi_column:
            return sorted(blocks, key=lambda b: (b.bbox.y0, b.bbox.x0))

        # Reorder: headers/spanning before, then col1, then col2, then footers
        col1_blocks.sort(key=lambda b: b.bbox.y0)
        col2_blocks.sort(key=lambda b: b.bbox.y0)

        # Integrate spanning blocks based on vertical position
        ordered: List[TextBlock] = []
        all_col_blocks = sorted(col1_blocks + col2_blocks, key=lambda b: b.bbox.y0)

        if not spanning_blocks:
            return col1_blocks + col2_blocks

        # For mixed layouts, split by top headers
        top_y = min((b.bbox.y0 for b in (col1_blocks + col2_blocks)), default=0)
        bottom_y = max((b.bbox.y1 for b in (col1_blocks + col2_blocks)), default=1e6)

        top_spanning = [b for b in spanning_blocks if b.bbox.y1 <= top_y + 10]
        middle_spanning = [b for b in spanning_blocks if b.bbox.y1 > top_y + 10 and b.bbox.y0 < bottom_y - 10]
        bottom_spanning = [b for b in spanning_blocks if b.bbox.y0 >= bottom_y - 10]

        top_spanning.sort(key=lambda b: b.bbox.y0)
        middle_spanning.sort(key=lambda b: b.bbox.y0)
        bottom_spanning.sort(key=lambda b: b.bbox.y0)

        ordered.extend(top_spanning)
        ordered.extend(col1_blocks)
        ordered.extend(middle_spanning)
        ordered.extend(col2_blocks)
        ordered.extend(bottom_spanning)

        return ordered

    @classmethod
    def assemble_page_flow(
        cls,
        text_blocks: List[TextBlock],
        tables: List[ExtractedTable],
        images: List[ExtractedImage],
        page_width: float,
    ) -> List[PageLayoutElement]:
        """Combine text blocks, tables, and images in top-to-bottom reading order."""
        body_font_size = cls.calculate_body_font_size(text_blocks)
        cls.classify_headings_and_styles(text_blocks, body_font_size)

        sorted_text = cls.detect_multi_column_order(text_blocks, page_width)

        elements: List[PageLayoutElement] = []

        for b in sorted_text:
            etype = "heading" if b.is_heading else ("list_item" if b.is_list_item else "paragraph")
            elements.append(PageLayoutElement(
                element_type=etype,
                content=b,
                y0=b.bbox.y0,
                x0=b.bbox.x0,
            ))

        for t in tables:
            elements.append(PageLayoutElement(
                element_type="table",
                content=t,
                y0=t.bbox.y0,
                x0=t.bbox.x0,
            ))

        for img in images:
            elements.append(PageLayoutElement(
                element_type="image",
                content=img,
                y0=img.bbox.y0,
                x0=img.bbox.x0,
            ))

        # Sort combined stream by vertical coordinate y0
        elements.sort(key=lambda el: (el.y0, el.x0))
        return elements
