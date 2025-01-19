from transformers import pipeline
from app.pdf_processing import split_into_chunks

# Load the question-answering model
qa_pipeline = pipeline("question-answering", model="deepset/roberta-base-squad2", device=0)  # Use GPU (cuda:0)


def find_exact_match(question, pdf_content):
    """Search for an exact match of the question in the text."""
    lines = pdf_content.split("\n")
    for line in lines:
        if question.lower() in line.lower():
            return line
    return None


def find_best_answer_or_related_matches(question, pdf_content, confidence_threshold=0.5, top_n=5):
    """Find the best answer or related matches for the question."""
    content = pdf_content
    # Find exact match (if available)
    exact_match = find_exact_match(question, content)
    if exact_match:
        content = exact_match  # Use the content with the exact match

    # Split the content into chunks
    chunks = split_into_chunks(content)

    # Initialize variables to store best answers and all answers
    best_answer = None
    best_score = 0
    all_answers = []

    for chunk in chunks:
        if not chunk.strip():  # Skip empty chunks
            continue
        try:
            result = qa_pipeline(question=question, context=chunk)
            print(f"Chunk: {chunk[:200]}...")  # Print the first 200 characters of the chunk
            print(f"Answer: {result['answer']}, Score: {result['score']}")  # Print the answer and score
            all_answers.append((result["answer"], result["score"], chunk))

            if result["score"] > best_score:
                best_answer = result["answer"]
                best_score = result["score"]

        except Exception as e:
            print(f"Error processing chunk: {e}")

    # If a confident answer is found, return it
    if best_answer and best_score >= confidence_threshold:
        return f"Answer: {best_answer} (Confidence: {best_score:.2f})"
    else:
        # If no confident answer is found, return the top 5 related answers
        sorted_answers = sorted(all_answers, key=lambda x: x[1], reverse=True)
        top_matches = [answer for answer, score, chunk in sorted_answers if score >= confidence_threshold]

        if len(top_matches) > 0:
            return "Sorry, I couldn't find a confident answer. Here are the top 5 related matches:\n" + "\n\n".join(
                top_matches[:top_n])
        else:
            return "Sorry, I couldn't find any relevant information."
