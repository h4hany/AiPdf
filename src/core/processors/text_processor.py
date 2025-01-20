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

    def split_into_chunks(self, text, max_length=1024, overlap=200):
        """Split text into overlapping chunks while preserving logical sections."""
        sections = text.split("\n\n")  # Split by double newlines (paragraphs)
        chunks = []
        current_chunk = ""

        for section in sections:
            # If adding this section would exceed the max_length, finalize the current chunk
            if len(current_chunk) + len(section) > max_length:
                if current_chunk.strip():  # Only add non-empty chunks
                    chunks.append(current_chunk.strip())
                current_chunk = ""

            # Add the section to the current chunk
            current_chunk += section + "\n\n"

        # Add the last chunk if it's not empty
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        # Apply overlapping to the chunks
        overlapping_chunks = []
        for i in range(0, len(chunks), max_length - overlap):
            overlapping_chunk = " ".join(chunks[i:i + max_length])
            if overlapping_chunk.strip():  # Only add non-empty chunks
                overlapping_chunks.append(overlapping_chunk)

        return overlapping_chunks
