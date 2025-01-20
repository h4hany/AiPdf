import logging
from src.services.qa_service import QAService


def main():
    # Configure logging
    # logging.basicConfig(level=logging.DEBUG)
    # logger = logging.getLogger(__name__)

    # Initialize QA service
    qa_service = QAService(enable_ocr=True)

    # PDF path
    pdf_path = "static/Absolent Air Care Group AB_F1ABA1.pdf"

    try:
        # Initialize with PDF
        qa_service.initialize(pdf_path)

        # Your questions
        questions = [
            "what is company name?",
            "what is Scope 1 CO2e emissions?",
            "how many net sales in 2021?",
            "how many number of employee ",
            "how many brands?",
            "Net sales, SEK thousands in 2021?"
            # Add more questions here
        ]

        # Get answers
        answers = qa_service.get_answers(questions)
        print('---------------------')
        # Print results
        for answer in answers:
            print(f"Question: {answer['question']}")
            print(f"Answer: {answer['answer']}")
            print(f"Confidence: {answer['confidence']:.2f}")
            print(f"context_type: {answer['context_type']}")
            print('---------------------')

    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
    finally:
        qa_service.cleanup()


if __name__ == "__main__":
    main()
