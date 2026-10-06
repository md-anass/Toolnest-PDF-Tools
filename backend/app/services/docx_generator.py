import io
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

from app.services.pdf_text_extractor import TextBlock, TextLine, TextSpan
from app.services.image_extractor import ExtractedImage
from app.services.layout_analyzer import PageLayoutElement, ExtractedTable
from app.models.conversion import ExtractedElements

logger = logging.getLogger(__name__)

# Max printable width in inches (8.5in page - 1.5in margins = 7.0in max)
MAX_IMAGE_WIDTH_INCHES = 6.0
MAX_IMAGE_HEIGHT_INCHES = 8.5


def set_cell_shading(cell, color_hex: str):
    """Set background color of a table cell."""
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Set inner padding for a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)


class DOCXGenerator:
    """Generates clean, editable Word documents (.docx) preserving layout and structure."""

    def __init__(self):
        self.doc = Document()
        self._configure_document()
        self.stats = ExtractedElements()

    def _configure_document(self):
        """Set standard page margins and default styles."""
        for section in self.doc.sections:
            section.top_margin = Inches(0.8)
            section.bottom_margin = Inches(0.8)
            section.left_margin = Inches(0.8)
            section.right_margin = Inches(0.8)
            section.page_width = Inches(8.5)
            section.page_height = Inches(11.0)

        # Configure normal style
        style = self.doc.styles['Normal']
        font = style.font
        font.name = 'Calibri'
        font.size = Pt(11)
        font.color.rgb = RGBColor(0x1F, 0x29, 0x37)  # Slate 800

    def add_heading(self, block: TextBlock):
        """Add a formatted heading with appropriate level and spacing."""
        level = max(1, min(block.heading_level, 3))
        p = self.doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12 if level == 1 else (8 if level == 2 else 6))
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True

        self._apply_alignment(p, block.alignment)

        # Use primary heading font sizes
        default_sizes = {1: Pt(20), 2: Pt(15), 3: Pt(12.5)}
        heading_color = RGBColor(0x0F, 0x17, 0x2A)  # Slate 900

        for line in block.lines:
            for span in line.spans:
                run = p.add_run(span.text)
                run.bold = True
                run.italic = span.is_italic
                run.font.size = default_sizes.get(level, Pt(14))
                run.font.name = 'Calibri'
                run.font.color.rgb = heading_color

        self.stats.headings += 1

    def add_paragraph(self, block: TextBlock):
        """Add a standard paragraph with run-level styles and font attributes."""
        p = self.doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15

        self._apply_alignment(p, block.alignment)

        for line_idx, line in enumerate(block.lines):
            for span in line.spans:
                run = p.add_run(span.text)
                run.bold = span.is_bold
                run.italic = span.is_italic

                # Clamp font size to reasonable bounds (8 to 36)
                clamped_size = max(8.0, min(span.font_size, 36.0))
                run.font.size = Pt(clamped_size)
                run.font.name = 'Calibri'

                # Preserve color if not plain black
                if span.color and span.color != 0:
                    r = (span.color >> 16) & 0xFF
                    g = (span.color >> 8) & 0xFF
                    b = span.color & 0xFF
                    # If not too light
                    if (r + g + b) < 680:
                        run.font.color.rgb = RGBColor(r, g, b)

            # If there are multiple lines within the same block, add a space if needed
            if line_idx < len(block.lines) - 1 and not line.text.endswith(" "):
                p.add_run(" ")

        self.stats.paragraphs += 1

    def add_list_item(self, block: TextBlock):
        """Add a list item with bullet indentation."""
        p = self.doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(2)

        # Remove leading bullet characters from text if present
        clean_lines = []
        for line in block.lines:
            line_copy = []
            for span in line.spans:
                txt = span.text
                if block.bullet_char and txt.startswith(block.bullet_char):
                    txt = txt[len(block.bullet_char):].strip()
                line_copy.append((txt, span))
            clean_lines.append(line_copy)

        for line_data in clean_lines:
            for txt, span in line_data:
                if not txt:
                    continue
                run = p.add_run(txt)
                run.bold = span.is_bold
                run.italic = span.is_italic
                run.font.size = Pt(max(8.0, min(span.font_size, 14.0)))
                run.font.name = 'Calibri'

        self.stats.lists += 1

    def add_table(self, table_data: ExtractedTable):
        """Add a formatted Word table."""
        rows = table_data.data
        if not rows or len(rows) == 0:
            return

        num_rows = len(rows)
        num_cols = max(len(r) for r in rows)
        if num_cols == 0:
            return

        table = self.doc.add_table(rows=num_rows, cols=num_cols)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.style = 'Table Grid'

        for r_idx, row in enumerate(rows):
            is_header = (r_idx == 0)
            for c_idx in range(num_cols):
                cell_text = str(row[c_idx] or "").strip() if c_idx < len(row) else ""
                cell = table.cell(r_idx, c_idx)
                cell.text = cell_text

                # Formatting cell paragraph
                p = cell.paragraphs[0]
                p.paragraph_format.space_before = Pt(2)
                p.paragraph_format.space_after = Pt(2)

                for run in p.runs:
                    run.font.name = 'Calibri'
                    run.font.size = Pt(10)
                    if is_header:
                        run.bold = True
                        run.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

                if is_header:
                    set_cell_shading(cell, "F1F5F9")  # Slate 100 header shading

                set_cell_margins(cell, top=120, bottom=120, left=150, right=150)

        # Add small spacing after table
        spacer = self.doc.add_paragraph()
        spacer.paragraph_format.space_before = Pt(4)
        spacer.paragraph_format.space_after = Pt(6)

        self.stats.tables += 1

    def add_image(self, extracted_img: ExtractedImage):
        """Insert image preserving aspect ratio within printable margins."""
        try:
            image_stream = io.BytesIO(extracted_img.image_bytes)

            # Calculate proportional dimensions
            img_width_px = max(extracted_img.width, 1)
            img_height_px = max(extracted_img.height, 1)
            aspect_ratio = img_height_px / img_width_px

            # Determine width in inches based on bounding box or standard sizing
            target_width = MAX_IMAGE_WIDTH_INCHES
            if extracted_img.bbox.width > 0:
                # 72 points per inch
                pt_width_inches = extracted_img.bbox.width / 72.0
                target_width = min(pt_width_inches, MAX_IMAGE_WIDTH_INCHES)

            target_width = max(target_width, 1.5)
            target_height = target_width * aspect_ratio

            if target_height > MAX_IMAGE_HEIGHT_INCHES:
                target_height = MAX_IMAGE_HEIGHT_INCHES
                target_width = target_height / aspect_ratio

            p = self.doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)

            p.add_run().add_picture(
                image_stream,
                width=Inches(target_width),
                height=Inches(target_height),
            )
            self.stats.images += 1

        except Exception as e:
            logger.warning(f"Error inserting image into docx: {e}")

    def add_page_break(self):
        """Add page break to separate PDF pages cleanly."""
        self.doc.add_page_break()

    def _apply_alignment(self, paragraph, alignment: str):
        if alignment == "center":
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif alignment == "right":
            paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        elif alignment == "justify":
            paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        else:
            paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT

    def save(self, output_path: str) -> None:
        """Save generated Word document to specified file path."""
        self.doc.save(output_path)
