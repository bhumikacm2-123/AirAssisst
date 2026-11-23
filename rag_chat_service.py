
import os
from dotenv import load_dotenv
from google import genai

from retrieve_knowledge import retrieve_knowledge

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file!")

client = genai.Client(api_key=api_key)

MODEL_NAME = "gemini-3.5-flash-lite"


def generate_rag_answer(question):
    """Generate an answer using retrieved AirAssist knowledge."""

    question = question.strip()

    if not question:
        return {
            "status": "error",
            "answer": "Please enter a question.",
            "sources": []
        }

    try:
        # Retrieve relevant knowledge
        results = retrieve_knowledge(
            question,
            top_k=3,
            threshold=0.10
        )

        if not results:
            return {
                "status": "success",
                "answer": "I could not find enough information in the AirAssist knowledge base to answer this question.",
                "sources": []
            }

        context = "\n\n".join(
            f"Source: {item['source']}\n{item['text']}"
            for item in results
        )

        prompt = f"""
You are AirAssist, an air-quality information assistant
focused on Indian cities.

Answer clearly using the knowledge context below.

Rules:
- Use the retrieved context as your primary source.
- Do not invent AQI values or pollution measurements.
- Explain when the available information is insufficient.
- Give general educational health precautions.
- Do not diagnose medical conditions.

KNOWLEDGE CONTEXT:
{context}

USER QUESTION:
{question}
"""

        interaction = client.interactions.create(
            model=MODEL_NAME,
            input=prompt
        )

        answer = interaction.output_text

        return {
            "status": "success",
            "answer": answer or "Sorry, I could not generate an answer.",
            "sources": list(dict.fromkeys(
                item["source"] for item in results
            ))
        }

    except Exception as error:
        print("AirAssist RAG error:", error)

        return {
            "status": "error",
            "answer": "AirAssist is temporarily unable to generate an answer. Please try again.",
            "sources": []
        }
