from transformers import AutoTokenizer, AutoModelForQuestionAnswering
import torch
from typing import Dict, Any
import logging


class QAModel:
    """Handles the question-answering model operations"""

    def __init__(self):
        self.model_name = "deepset/bert-large-uncased-whole-word-masking-squad2"
        self.tokenizer = None
        self.model = None
        self.max_length = 512
        self.stride = 128
        self.max_context_size = 1000  # Limit context size for faster processing
        self.device = 0
        self.load_model()

    def load_model(self):
        """Loads the QA model and tokenizer"""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForQuestionAnswering.from_pretrained(self.model_name)
            # Move model to GPU if available
            if torch.cuda.is_available():
                self.model = self.model.cuda()
            logging.getLogger("transformers.modeling_utils").setLevel(logging.ERROR)
        except Exception as e:
            raise Exception(f"Error loading model: {str(e)}")

    def preprocess_context(self, context: str) -> str:
        """Preprocess the context to make it more QA-friendly"""
        # Basic cleaning
        context = " ".join(context.split())
        context = context.replace("\n", ". ")
        context = context.replace("..", ".")
        # Limit context size
        return context[:self.max_context_size]

    def get_answer(self, question: str, context: str) -> Dict[str, Any]:
        """Gets answer for a question from given context"""
        if not self.model or not self.tokenizer:
            raise Exception("Model not loaded")

        # Preprocess the context
        context = self.preprocess_context(context)

        # Tokenize input
        encoding = self.tokenizer(
            question,
            context,
            max_length=self.max_length,
            truncation='only_second',
            return_tensors="pt"
        )

        # Move inputs to GPU if available
        if torch.cuda.is_available():
            encoding = {k: v.cuda() for k, v in encoding.items()}

        # Get model output
        outputs = self.model(**encoding)

        # Get start and end logits
        start_logits = outputs.start_logits[0]
        end_logits = outputs.end_logits[0]

        # Get best answer span
        start_idx = torch.argmax(start_logits)
        end_idx = torch.argmax(end_logits)

        # Convert to CPU for numpy operations
        if torch.cuda.is_available():
            start_idx = start_idx.cpu()
            end_idx = end_idx.cpu()

        # Get confidence score
        confidence = float(torch.max(start_logits) + torch.max(end_logits))

        # Get answer tokens
        input_ids = encoding["input_ids"][0]
        tokens = self.tokenizer.convert_ids_to_tokens(input_ids)

        # Convert tokens to answer text
        if end_idx >= start_idx:
            answer_tokens = tokens[start_idx:end_idx + 1]
            answer = self.tokenizer.convert_tokens_to_string(answer_tokens)
        else:
            answer = ""

        # Clean up the answer
        answer = answer.strip()
        answer = answer.replace("[CLS]", "").replace("[SEP]", "").strip()

        if not answer:
            return {
                "answer": "No answer found",
                "score": 0.0,
                "start": 0,
                "end": 0
            }

        return {
            "answer": answer,
            "score": confidence,
            "start": int(start_idx),
            "end": int(end_idx)
        }
