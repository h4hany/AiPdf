from typing import Dict, Any
import pdfplumber
import logging
import re

class PDFExtractor:
    """Handles extraction of content from PDF"""
    
    def __init__(self, enable_ocr: bool = False):
        self.logger = logging.getLogger(__name__)
        self.pdf = None
        self.enable_ocr = enable_ocr
        # self.table_processor = TableProcessor()
    
    def load_pdf(self, pdf_path: str) -> None:
        """Loads PDF file"""
        try:
            self.pdf = pdfplumber.open(pdf_path)
        except Exception as e:
            raise Exception(f"Error loading PDF: {str(e)}")
    
    def extract_content(self) -> str:
        """Extract all content from PDF"""
        if not self.pdf:
            raise Exception("PDF not loaded")
            
        try:
            content = ""
            for page in self.pdf.pages:
                # Extract text from page
                text = page.extract_text()
                if text:
                    content += text + "\n\n"

            # Basic cleaning while preserving important content
            content = re.sub(r'\s+', ' ', content)  # Normalize whitespace
            content = content.replace('|', ' ')     # Remove vertical bars
            content = content.strip()               # Remove leading/trailing whitespace

            # self.logger.debug(f"Extracted content length: {len(content)}")
            return content
            
        except Exception as e:
            self.logger.error(f"Error extracting content: {str(e)}")
            return ""


    def extract_tables(self) -> str:
        """Extract tables from PDF"""
        if not self.pdf:
            raise Exception("PDF not loaded")
            
        try:
            # Use table processor to extract tables
            table_content = self.table_processor.process_tables(self.pdf.pages)
            self.logger.debug(f"Extracted table content length: {len(table_content)}")
            return table_content
            
        except Exception as e:
            self.logger.error(f"Error extracting tables: {str(e)}")
            return ""
    
    def close(self):
        """Close the PDF file"""
        if self.pdf:
            self.pdf.close() 