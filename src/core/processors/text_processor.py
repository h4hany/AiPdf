import logging
import re


class TextProcessor:
    """Handles text extraction and processing from PDF pages"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

    def clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""
        """Clean and preprocess the extracted text."""
        # Remove extra spaces and special characters
        text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with a single space
        text = re.sub(r'[^\x00-\x7F]+', ' ', text)  # Remove non-ASCII characters
        # Remove bullet points and other formatting artifacts
        text = re.sub(r'▪', '', text)  # Remove bullet points
        text = re.sub(r'\d+\.\d+', '', text)  # Remove decimal numbers (if irrelevant)
        text = re.sub(r'[\(\[].*?[\)\]]', '', text)  # Remove text inside parentheses or brackets
        text = re.sub(r'\b(?:page|pages?|section|question|answer)\b', '', text,
                      flags=re.I)  # Remove irrelevant keywords like 'page', 'question', etc.
        return text

