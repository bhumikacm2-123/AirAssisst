
import json
import pickle

from sklearn.metrics.pairwise import cosine_similarity

print("AirAssist Knowledge Retrieval started!")

# Step 1: Load the saved TF-IDF vectorizer
with open(
    "data/vector_store/tfidf_vectorizer.pkl", "rb"
) as file:
    vectorizer = pickle.load(file)

# Step 2: Load the TF-IDF matrix
with open(
    "data/vector_store/tfidf_matrix.pkl", "rb"
) as file:
    tfidf_matrix = pickle.load(file)

# Step 3: Load knowledge chunks
with open(
    "data/vector_store/chunks.json",
    "r",
    encoding="utf-8"
) as file:
    chunks = json.load(file)


# Step 4: Retrieve relevant knowledge
def retrieve_knowledge(question, top_k=3, threshold=0.10):

    print("\nSearching knowledge base...")
    print("Question:", question)

    # Convert question into TF-IDF vector
    question_vector = vectorizer.transform([question])

    # Calculate cosine similarity
    scores = cosine_similarity(
        question_vector,
        tfidf_matrix
    )[0]

    # Sort results by similarity
    ranked_indices = scores.argsort()[::-1]

    results = []

    for index in ranked_indices:

        # Ignore results below the threshold
        if scores[index] < threshold:
            continue

        results.append({
            "source": chunks[index].get(
                "source", "Unknown"
            ),
            "score": round(float(scores[index]), 4),
            "text": chunks[index]["text"]
        })

        if len(results) >= top_k:
            break

    return results


# Step 5: Test retrieval
if __name__ == "__main__":

    question = input(
        "\nAsk an air-quality question: "
    ).strip()

    if not question:
        print("\nPlease enter a question.")

    else:
        results = retrieve_knowledge(
            question,
            top_k=3,
            threshold=0.10
        )

        if results:

            print("\nRelevant Knowledge Found:")

            for number, result in enumerate(
                results, start=1
            ):

                print(f"\n--- Result {number} ---")
                print("Source:", result["source"])
                print("Similarity:", result["score"])
                print("\nInformation:")
                print(result["text"])

        else:
            print("\nNo relevant information found.")
            print("Try asking another air-quality question.")

    print("\nAirAssist Knowledge Retrieval completed!")
