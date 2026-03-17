import re
import io
import fitz  # PyMuPDF
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import Color
from reportlab.pdfbase.pdfmetrics import stringWidth
from app.translator import Translator


class PDFProcessor:
    def __init__(self):
        self.translator = Translator()
        self.chinese_font = None
        local_font = Path(__file__).parent / "fonts" / "NotoSansSC-Regular.ttf"
        font_paths = [
            str(local_font),
            '/System/Library/Fonts/PingFang.ttc',
            '/System/Library/Fonts/STHeiti Light.ttc',
            '/System/Library/Fonts/STHeiti Medium.ttc',
            '/System/Library/Fonts/Hiragino Sans GB.ttc',
        ]
        
        for fp in font_paths:
            try:
                if Path(fp).exists():
                    pdfmetrics.registerFont(TTFont('ChineseFont', fp))
                    self.chinese_font = 'ChineseFont'
                    print(f"Registered font: {fp}")
                    break
            except Exception as e:
                print(f"Failed to register {fp}: {e}")
                continue
        
        if not self.chinese_font:
            self.chinese_font = 'Helvetica'
            print("Warning: No Chinese font available")

    def process_pdf(self, input_path: Path, output_path: Path) -> dict:
        try:
            reader = PdfReader(str(input_path))
            writer = PdfWriter()
            
            doc = fitz.open(str(input_path))
            pages_processed = len(doc)
            pages_translated = 0

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                
                if self._contains_comment_keyword(text):
                    overlay = self._create_translation_overlay(page)
                    if overlay:
                        page_obj = reader.pages[page_num]
                        page_obj.merge_page(overlay.pages[0])
                        writer.add_page(page_obj)
                    else:
                        writer.add_page(reader.pages[page_num])
                    pages_translated += 1
                else:
                    writer.add_page(reader.pages[page_num])

            doc.close()

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
            return {"success": False, "error": str(e)}

    def _contains_comment_keyword(self, text: str) -> bool:
        if not text:
            return False
        pattern = re.compile(r'\bcomments?\b', re.IGNORECASE)
        return bool(pattern.search(text))

    def _get_wrap_positions(self, text: str, max_width: float, font_size: float) -> list:
        """Split text into lines that fit within max_width"""
        if not text:
            return []
        
        # Estimate characters that fit per line (rough calculation)
        char_width = font_size * 0.6  # Approximate width per Chinese character
        chars_per_line = int(max_width / char_width)
        
        if chars_per_line <= 0:
            chars_per_line = 20
        
        lines = []
        for i in range(0, len(text), chars_per_line):
            lines.append(text[i:i + chars_per_line])
        
        return lines

    def _create_translation_overlay(self, page: fitz.Page):
        try:
            width = float(page.mediabox.width)
            height = float(page.mediabox.height)
            
            packet = io.BytesIO()
            c = canvas.Canvas(packet, pagesize=(width, height))
            
            text_dict = page.get_text("dict")
            
            # Track used Y positions to avoid overlap
            used_positions = []
            
            for block in text_dict.get("blocks", []):
                if block.get("type") != 0:
                    continue
                
                for line in block.get("lines", []):
                    line_text = ""
                    for span in line.get("spans", []):
                        line_text += span.get("text", "")
                    
                    line_text = line_text.strip()
                    if not line_text:
                        continue
                    
                    translated = self.translator.translate(line_text)
                    if not translated:
                        continue
                    
                    spans = line.get("spans", [])
                    if spans:
                        font_size = sum(s.get("size", 10) for s in spans) / len(spans)
                    else:
                        font_size = 10
                    
                    bbox = line.get("bbox", [0, 0, 0, 0])
                    
                    # Calculate available width for translation
                    x_pos = bbox[2] + 8  # Start position
                    available_width = width - x_pos - 20  # Right margin
                    
                    if available_width < 50:
                        available_width = 200  # Default fallback
                    
                    # Wrap translation if needed
                    trans_lines = self._get_wrap_positions(translated, available_width, font_size)
                    
                    # Draw each wrapped line
                    for idx, trans_line in enumerate(trans_lines):
                        y_pos = height - bbox[3] + 2 - (idx * font_size * 1.3)
                        
                        # Skip if this position is already used
                        pos_key = (round(x_pos), round(y_pos))
                        if pos_key in used_positions:
                            y_pos -= font_size * 1.3
                        used_positions.append(pos_key)
                        
                        c.setFillColor(Color(1, 0, 0, alpha=1))
                        c.setFont(self.chinese_font, font_size)
                        c.drawString(x_pos, y_pos, trans_line)
            
            c.save()
            packet.seek(0)
            
            return PdfReader(packet)
            
        except Exception as e:
            print(f"Error creating overlay: {e}")
            import traceback
            traceback.print_exc()
            return None
