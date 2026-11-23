
import os
from dotenv import load_dotenv
from google import genai

from retrieve_knowledge import retrieve_knowledge

# Load Gemini API key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("Gemini API key not found in .env file!")

client = genai.Client(api_key=api_key)

MODEL_NAME = "gemini-3.5-flash-lite"


def ask_airassist(question):
    print("\nSearching AirAssist knowledge base...")

    # Retrieve relevant information
    results = retrieve_knowledge(
        question,
        top_k=3,
        threshold=0.10
    )

    if not results:
        return (
            "I could not find enough information in my "
            "air-quality knowledge base to answer this question."
        )

    # Prepare retrieved context
    context = "\n\n".join(
        [
            f"Source: {item['source']}\n{item['text']}"
            for item in results
        ]
    )

    prompt = f"""
You are AirAssist, an air-quality information assistant
focused on Indian cities.

Answer the user's question using the provided knowledge.

Rules:
1. Give clear, simple and helpful answers.
2. Use the provided context as your primary source.
3. Do not invent pollution measurements or AQI values.
4. If the context does not contain enough information,
   clearly say so.
5. Give general educational health precautions only.
6. Do not claim to diagnose or treat medical conditions.

KNOWLEDGE CONTEXT:
{context}

USER QUESTION:
{question}

Provide a helpful answer:
"""

    try:
        interaction = client.interactions.create(
            model=MODEL_NAME,
            input=prompt
        )

        return interaction.output_text

    except Exception as error:
        print("\nGemini API error:", error)
        return (
            "Sorry, AirAssist could not generate an answer "
            "right now. Please try again later."
        )


if __name__ == "__main__":
    print("\n===================================")
    print("       AIRASSIST RAG CHATBOT")
    print("===================================")
    print("Ask questions about air quality.")
    print("Type 'exit' to stop.\n")

    while True:
        question = input("You: ").strip()

        if question.lower() in ["exit", "quit"]:
            print("\nThank you for using AirAssist!")
            break

        if not question:
            print("Please enter a question.")
            continue

        answer = ask_airassist(question)

        print("\nAirAssist:", answer)
        print("\n-----------------------------------")
