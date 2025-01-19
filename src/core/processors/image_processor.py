import logging
from typing import List, Optional
from PIL import Image
import io

class ImageProcessor:
    """Handles image extraction and OCR from PDF pages"""
    
    def __init__(self, enable_ocr: bool = False):
        self.logger = logging.getLogger(__name__)
        self.enable_ocr = enable_ocr
        self.tesseract_available = False
        
        if enable_ocr:
            try:
                import pytesseract
                self.pytesseract = pytesseract
                self.tesseract_available = True
            except ImportError:
                self.logger.warning("pytesseract not installed. OCR features will be disabled.")
            except Exception as e:
                self.logger.warning(f"Error initializing tesseract: {str(e)}. OCR features will be disabled.")
    
    def process_images(self, pages) -> List[str]:
        """Extract and process images from PDF pages"""
        images_text = []
        
        if not self.enable_ocr or not self.tesseract_available:
            return images_text
            
        try:
            for page in pages:
                for image in page.images:
                    try:
                        img = Image.open(io.BytesIO(image['stream'].get_data()))
                        text = self.pytesseract.image_to_string(img)
                        if text.strip():
                            images_text.append(text)
                    except Exception as e:
                        self.logger.error(f"Error processing image: {str(e)}")
                        continue
            return images_text
        except Exception as e:
            self.logger.error(f"Error processing images: {str(e)}")
            return images_text 