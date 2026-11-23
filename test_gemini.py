
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("Gemini API key not found!")

client = genai.Client(api_key=api_key)

print("Connecting to Gemini API...")

try:
    interaction = client.interactions.create(
        model="gemini-3.5-flash-lite",
        input="Say: AirAssist Gemini connection successful!"
    )

    print("\nGemini API connection successful!")
    print(interaction.output_text)

except Exception as error:
    print("\nGemini API request failed:")
    print(error)
