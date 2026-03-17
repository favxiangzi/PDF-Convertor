import re
import io
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import Color
from app.translator import Translator


class PDFProcessor:
    def __init__(self):
        self.translator = Translator()
        # Register Chinese font
        try:
            pdfmetrics.registerFont(TTFont('Chinese', '/System/Library/Fonts/STHeiti Light.ttc'))
            self.chinese_font = 'Chinese'
        except Exception as e:
            print(f"Warning: Could not register Chinese font: {e}")
            self.chinese_font = 'Helvetica'

    def process_pdf(self, input_path: Path, output_path: Path) -> dict:
        """
        Process PDF file: detect comment pages, translate, and add Chinese text.
        """
        try:
            reader = PdfReader(str(input_path))
            writer = PdfWriter()
            
            pages_processed = len(reader.pages)
            pages_translated = 0

            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                
                # Extract text
                text = page.extract_text()
                
                if self._contains_comment_keyword(text):
                    # Create overlay with translations
                    overlay = self._create_translation_overlay(page, text)
                    if overlay:
                        page.merge_page(overlay.pages[0])
                    pages_translated += 1
                
                writer.add_page(page)

            with open(output_path, 'wb') as f:
                writer.write(f)

            return {
                "success": True,
                "pages_processed": pages_processed,
                "pages_translated": pages_translated
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }

    def _contains_comment_keyword(self, text: str) -> bool:
        if not text:
            return False
        pattern = re.compile(r'\bcomments?\b', re.IGNORECASE)
        return bool(pattern.search(text))

    def _create_translation_overlay(self, page, text: str):
        """
        Create an overlay PDF with Chinese translations in RED.
        """
        try:
            # Get page dimensions
            width = float(page.mediabox.width)
            height = float(page.mediabox.height)
            
            # Create overlay PDF
            packet = io.BytesIO()
            c = canvas.Canvas(packet, pagesize=(width, height))
            
            # Set font for Chinese text - RED color
            c.setFillColor(Color(1, 0, 0, alpha=1))  # Red
            c.setFont(self.chinese_font, 10)
            
            # Extract text lines with layout
            try:
                # Try to get text with layout info
                text_dict = page.get_text("dict")
                lines = []
                for block in text_dict.get("blocks", []):
                    if block.get("type") != 0:
                        continue
                    for line in block.get("lines", []):
                        line_text = ""
                        for span in line.get("spans", []):
                            line_text += span.get("text", "")
                        bbox = line.get("bbox", [0, 0, 0, 0])
                        lines.append({
                            'text': line_text,
                            'y': height - bbox[3],  # Convert to reportlab coordinates
                            'height': bbox[3] - bbox[1]
                        })
            except:
                # Fallback: simple line extraction
                lines = []
                y = height - 50
                for line_text in text.split('\n'):
                    if line_text.strip():
                        lines.append({'text': line_text, 'y': y, 'height': 12})
                    y -= 14
            
            # Process each line and add translation on the right
            for line_data in lines:
                line_text = line_data['text'].strip()
                if not line_text:
                    continue
                
                # Translate
                translated = self.translator.translate(line_text)
                if not translated:
                    continue
                
                # Position: right side of page (55% width)
                trans_x = width * 0.55
                trans_y = line_data['y']
                
                # Adjust font size to match original (slightly smaller for Chinese)
                font_size = max(line_data['height'] * 0.8, 8)
                
                # Draw Chinese translation in RED
                c.setFillColor(Color(1, 0, 0, alpha=1))
                c.setFont(self.chinese_font, font_size)
                c.drawString(trans_x, trans_y, translated)
            
            c.save()
            packet.seek(0)
            
            return PdfReader(packet)
            
        except Exception as e:
            print(f"Error creating overlay: {e}")
            import traceback
            traceback.print_exc()
            return None