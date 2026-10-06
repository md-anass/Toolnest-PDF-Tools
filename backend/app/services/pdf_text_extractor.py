import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


@dataclass
class TextSpan:
    text: str
    font_name: str
    font_size: float
    is_bold: bool
    is_italic: bool
    color: int  # sRGB integer or hex
    bbox: fitz.Rect  # (x0, y0, x1, y1)


@dataclass
class TextLine:
    spans: List[TextSpan] = field(default_factory=list)
    bbox: fitz.Rect = field(default_factory=lambda: fitz.Rect(0, 0, 0, 0))
    text: str = ""


@dataclass
class TextBlock:
    lines: List[TextLine] = field(default_factory=list)
    bbox: fitz.Rect = field(default_factory=lambda: fitz.Rect(0, 0, 0, 0))
    text: str = ""
    alignment: str = "left"  # left, center, right, justify
    is_heading: bool = False
    heading_level: int = 0  # 1 for H1, 2 for H2, 3 for H3
    is_list_item: bool = False
    bullet_char: str = ""


class PDFTextExtractor:
    """Extracts rich text structures (spans, font attributes, lines, blocks) using PyMuPDF dict layout."""

    @staticmethod
    def extract_blocks_from_page(page: fitz.Page, page_width: float) -> List[TextBlock]:
        """Extract text blocks with font sizes, weights, and styles preserved."""
        # Use page.get_text("dict") for deep layout representation
        page_dict = page.get_text("dict")
        blocks: List[TextBlock] = []

        raw_blocks = page_dict.get("blocks", [])

        for b in raw_blocks:
            # Block type 0 is text (type 1 is image)
            if b.get("type") != 0:
                continue

            block_rect = fitz.Rect(b.get("bbox", (0, 0, 0, 0)))
            text_lines: List[TextLine] = []
            block_full_text = []

            for line_data in b.get("lines", []):
                line_rect = fitz.Rect(line_data.get("bbox", (0, 0, 0, 0)))
                spans: List[TextSpan] = []
                line_full_text = []

                for span_data in line_data.get("spans", []):
                    span_text = span_data.get("text", "")
                    if not span_text:
                        continue

                    font_name = span_data.get("font", "")
                    font_size = float(span_data.get("size", 11.0))
                    flags = span_data.get("flags", 0)
                    color = span_data.get("color", 0)
                    span_rect = fitz.Rect(span_data.get("bbox", (0, 0, 0, 0)))

                    # PyMuPDF font flags: bit 1 is italic (2), bit 4 is bold (16)
                    is_bold = bool(flags & 16) or ("bold" in font_name.lower()) or ("black" in font_name.lower())
                    is_italic = bool(flags & 2) or ("italic" in font_name.lower()) or ("oblique" in font_name.lower())

                    spans.append(
                        TextSpan(
                            text=span_text,
                            font_name=font_name,
                            font_size=round(font_size, 1),
                            is_bold=is_bold,
                            is_italic=is_italic,
                            color=color,
                            bbox=span_rect,
                        )
                    )
                    line_full_text.append(span_text)

                if spans:
                    joined_line = "".join(line_full_text).strip()
                    if joined_line:
                        text_lines.append(
                            TextLine(
                                spans=spans,
                                bbox=line_rect,
                                text=joined_line,
                            )
                        )
                        block_full_text.append(joined_line)

            if text_lines:
                combined_text = "\n".join(block_full_text).strip()
                if combined_text:
                    # Detect block alignment relative to page width
                    left_margin = block_rect.x0
                    right_margin = page_width - block_rect.x1
                    margin_diff = abs(left_margin - right_margin)

                    alignment = "left"
                    # If left and right margins are roughly equal and margins are noticeable (> 50pt)
                    if margin_diff < 40 and left_margin > 60 and block_rect.width < (page_width * 0.75):
                        alignment = "center"
                    elif right_margin < 50 and left_margin > (page_width * 0.4):
                        alignment = "right"

                    # Check for bullet or list marker
                    is_list = False
                    bullet = ""
                    first_char = combined_text[:2].strip()
                    if first_char in ["•", "-", "*", "–", "—", "›", "»"]:
                        is_list = True
                        bullet = first_char
                    elif len(combined_text) > 3 and combined_text[0].isdigit() and combined_text[1:3] in [". ", ") "]:
                        is_list = True
                        bullet = combined_text[:2]

                    blocks.append(
                        TextBlock(
                            lines=text_lines,
                            bbox=block_rect,
                            text=combined_text,
                            alignment=alignment,
                            is_list_item=is_list,
                            bullet_char=bullet,
                        )
                    )

        return blocks
