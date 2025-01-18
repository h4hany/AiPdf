from app.pdf_processing import extract_text_from_pdf, preprocess_text
from app.qa_processing import find_best_answer_or_related_matches


def main():
    print("Welcome to the Generic PDF Question Answering App!")
    pdf_path = input("Enter the path to your PDF file: ")

    # Extract and preprocess text from the PDF
    raw_text = extract_text_from_pdf('app/static/hany_sayed_cv.pdf')
    if not raw_text:
        print("Could not extract text from the PDF. Exiting...")
        return

    pdf_content = preprocess_text(raw_text)
    print("\nPDF loaded and preprocessed successfully. You can now ask questions.")
    print("Type 'exit' to quit the application.\n")

    # Interactive question-answering loop
    while True:
        question = input("Your Question: ")
        if question.lower() == "exit":
            print("Exiting the application. Goodbye!")
            break

        try:
            response = find_best_answer_or_related_matches(question, pdf_content)
            print(response + "\n")
        except Exception as e:
            print(f"Error processing the question: {e}\n")


if __name__ == "__main__":
    main()
