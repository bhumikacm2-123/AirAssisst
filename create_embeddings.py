
import json
import os
import pickle

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

print("AirAssist TF-IDF Vector Generation started!")

# Load knowledge chunks
input_file = "data/processed/knowledge_chunks.json"

with open(input_file, "r", encoding="utf-8") as file:
    chunks = json.load(file)

if not chunks:
    raise ValueError("No knowledge chunks found!")

print("Total text chunks:", len(chunks))

# Extract text
texts = [chunk["text"] for chunk in chunks]

# Generate TF-IDF vectors
print("\nGenerating TF-IDF vectors...")

vectorizer = TfidfVectorizer(
    stop_words="english",
    ngram_range=(1, 2)
)

tfidf_matrix = vectorizer.fit_transform(texts)

# Create storage folder
os.makedirs("data/vector_store", exist_ok=True)

# Save vectorizer and matrix
with open("data/vector_store/tfidf_vectorizer.pkl", "wb") as file:
    pickle.dump(vectorizer, file)

with open("data/vector_store/tfidf_matrix.pkl", "wb") as file:
    pickle.dump(tfidf_matrix, file)

# Save knowledge chunks
with open("data/vector_store/chunks.json", "w", encoding="utf-8") as file:
    json.dump(chunks, file, indent=4, ensure_ascii=False)

print("\nVector generation completed successfully!")
print("Number of chunks:", len(chunks))
print("TF-IDF matrix shape:", tfidf_matrix.shape)
print("Saved in: data/vector_store/")

print("\nAirAssist vector generation completed!")
