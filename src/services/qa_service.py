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
            self.table_content = self.pdf_extractor.extract_tables()
            self.image_content = self.pdf_extractor.extract_images()
            # self.logger.debug(f"Extracted table length: {len(self.table_content)}")

        except Exception as e:
            self.logger.error(f"Error initializing service: {str(e)}")
            raise

    def get_answers(self, questions: List[str]) -> List[Dict[str, Any]]:
        """Get answers for multiple questions"""
        self.logger.debug(f"Processing {len(questions)} questions")
        answers = []
        for question in questions:
            answer = self.find_answer(question)
            answers.append({
                "question": question,
                "answer": answer["answer"],
                "confidence": answer["confidence"],
                "context_type": answer["context_type"]
            })
        return answers

    def find_exact_match(self, question: str, content: str) -> str | None:
        """Search for an exact match of the question in the text"""
        lines = content.split("\n")
        for line in lines:
            if question.lower() in line.lower():
                return line
        return None

    def find_answer(self, question, confidence_threshold: float = 0.5):
        answer = self.find_best_answer_or_related_matches(question, self.table_content, "table")
        if not answer["is_found"]:
            answer = self.find_best_answer_or_related_matches(question, self.image_content, "image")
        elif not answer["is_found"]:
            answer = self.find_best_answer_or_related_matches(question, self.text_content, "text")
        # return answer
        # answer = self.find_best_answer_or_related_matches(question, self.text_content, "text")
        # answer = self.find_best_answer_or_related_matches(question, self.image_content, "image")
        # answer = self.find_best_answer_or_related_matches(question, self.table_content, "table")
        return answer



    def find_best_answer_or_related_matches(self, question: str, context: str, context_type: str = "",
                                            confidence_threshold: float = 0.5):
        """Get answer for a question from the content"""
        try:
            self.logger.debug(f"Processing question: {question}")

            if not context:
                self.logger.warning("No content available for processing")
                return {
                    "answer": "No content loaded",
                    "confidence": 0.0,
                    "context_type": context_type,
                    "is_found": False
                }

            content = context
            exact_match = self.find_exact_match(question, content)
            if exact_match:
                content = exact_match  # Use the content with the exact match

            chunks = self.text_processor.split_into_chunks(content)
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
                    "confidence": best_score,
                    "context_type": context_type,
                    "is_found": True

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
                        "confidence": 0.0,
                        "context_type": context_type,
                        "is_found": False
                    }

        except Exception as e:
            self.logger.error(f"Error in get_answer: {str(e)}")
            return {
                "answer": "Error processing question",
                "confidence": 0.0,
                "context_type": context_type,
                "is_found": False

            }

    def cleanup(self):
        """Clean up resources"""
        try:
            self.pdf_extractor.close()
        except Exception as e:
            self.logger.error(f"Error in cleanup: {str(e)}")
