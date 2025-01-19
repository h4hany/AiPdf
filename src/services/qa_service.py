from typing import List, Dict, Any
from ..core.pdf_extractor import PDFExtractor
from ..core.qa_model import QAModel
from ..core.processors.text_processor import TextProcessor
import logging
import re
from dataclasses import dataclass
from typing import List, Optional
from transformers import pipeline


@dataclass
class TableRow:
    header: str
    values: dict  # year -> value mapping


class QAService:
    """Service for question answering using transformer models"""

    def __init__(self, enable_ocr: bool = False):
        self.text_processor = None
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        self.logger.debug("Initializing QA pipeline...")
        self.qa_pipeline = pipeline(
            "question-answering",
            model="deepset/bert-large-uncased-whole-word-masking-squad2",
            device=0
        )

        self.pdf_extractor = PDFExtractor(enable_ocr=enable_ocr)
        self.text_content = ""
        self.table_content = ""
        self.image_content = ""
        self.parsed_tables = []  # List of lists of TableRow
        # self.qa_model = QAModel()
        self.combined_content = ""

    def initialize(self, pdf_path: str) -> None:
        """Initialize the service with a PDF file"""
        try:
            self.logger.debug(f"Loading PDF from: {pdf_path}")
            self.pdf_extractor.load_pdf(pdf_path)
            self.text_processor = TextProcessor()
            # self.logger.debug("Extracting text content...")
            self.text_content = self.text_processor.clean_text(self.pdf_extractor.extract_content())
            # self.logger.debug(f"Extracted text length: {len(self.text_content)}")

            # self.logger.debug("Extracting table content...")
            # self.table_content = self.pdf_extractor.extract_tables()
            # self.logger.debug(f"Extracted table length: {len(self.table_content)}")

            # Combine content for processing
            self.combined_content = f"{self.text_content}\n\n{self.table_content}"
            # self.logger.debug(f"Combined content length: {len(self.combined_content)}")

            # Log first 500 characters of content for debugging
            # self.logger.debug(f"Content preview: {self.combined_content[:500]}...")

        except Exception as e:
            self.logger.error(f"Error initializing service: {str(e)}")
            raise

    def get_answers(self, questions: List[str]) -> List[Dict[str, Any]]:
        """Get answers for multiple questions"""
        self.logger.debug(f"Processing {len(questions)} questions")
        answers = []
        for question in questions:
            answer = self.find_best_answer_or_related_matches(question)
            answers.append({
                "question": question,
                "answer": answer["answer"],
                "confidence": answer["confidence"]
            })
        return answers

    def find_exact_match(self, question: str, content: str) -> str:
        """Search for an exact match of the question in the text"""
        lines = content.split("\n")
        for line in lines:
            if question.lower() in line.lower():
                return line
        return None

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

    def find_best_answer_or_related_matches(self, question: str, confidence_threshold: float = 0.5):
        """Get answer for a question from the content"""
        try:
            self.logger.debug(f"Processing question: {question}")

            if not self.combined_content:
                self.logger.warning("No content available for processing")
                return {
                    "answer": "No content loaded",
                    "confidence": 0.0
                }

            content = self.combined_content
            exact_match = self.find_exact_match(question, content)
            if exact_match:
                content = exact_match  # Use the content with the exact match

            chunks = self.split_into_chunks(content)
            best_answer = None
            best_score = 0
            all_answers = []

            for chunk in chunks:
                if not chunk.strip():  # Skip empty chunks
                    continue
                try:
                    result = self.qa_pipeline(question=question, context=chunk)
                    # result = self.qa_model.get_answer(question, chunk)
                    # print(f"Chunk: {chunk[:200]}...")  # Print the first 200 characters of the chunk
                    # print(f"Answer: {result['answer']}, Score: {result['score']}")  # Print the answer and score
                    all_answers.append((result["answer"], result["score"], chunk))

                    if result["score"] > best_score:
                        best_answer = result["answer"]
                        best_score = result["score"]

                except Exception as e:
                    print(f"Error processing chunk: {e}")

            # If a confident answer is found, return it
            if best_answer and best_score >= confidence_threshold:
                return {
                    "answer": best_answer,
                    "confidence": best_score
                }
            else:
                # If no confident answer is found, return the top 5 related answers
                sorted_answers = sorted(all_answers, key=lambda x: x[1], reverse=True)
                # top_matches = [answer for answer, score, chunk in sorted_answers if score >= confidence_threshold]
                top_matches = [
                    {"answer": answer, "confidence": score, "chunk": chunk}
                    for answer, score, chunk in sorted_answers
                    if score >= confidence_threshold
                ]
                if len(top_matches) > 0:
                    return top_matches[0]
                else:
                    return {
                        "answer": "No answer found",
                        "confidence": 0.0
                    }

        except Exception as e:
            self.logger.error(f"Error in get_answer: {str(e)}")
            return {
                "answer": "Error processing question",
                "confidence": 0.0
            }

    def cleanup(self):
        """Clean up resources"""
        try:
            self.pdf_extractor.close()
        except Exception as e:
            self.logger.error(f"Error in cleanup: {str(e)}")
