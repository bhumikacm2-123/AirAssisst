
import json
from pathlib import Path

print("AirAssist Knowledge Processing started!")

# Folder containing the five knowledge documents
knowledge_folder = Path("data/knowledge_base")

# Output folder
output_folder = Path("data/processed")
output_folder.mkdir(parents=True, exist_ok=True)

# Chunk settings
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

all_chunks = []

# Find all Markdown documents
documents = list(knowledge_folder.glob("*.md"))

if not documents:
    print("No Markdown documents found!")
    raise SystemExit

print(f"\nFound {len(documents)} knowledge documents.")

for document in documents:

    print(f"\nProcessing: {document.name}")

    text = document.read_text(encoding="utf-8")

    # Split text into paragraphs
    paragraphs = [
        p.strip() for p in text.split("\n\n") if p.strip()
    ]

    current_chunk = ""

    for paragraph in paragraphs:

        if len(current_chunk) + len(paragraph) <= CHUNK_SIZE:
            current_chunk += paragraph + "\n\n"

        else:
            if current_chunk.strip():
                all_chunks.append({
                    "source": document.name,
                    "text": current_chunk.strip()
                })

            # Retain a small overlap from the previous chunk
            overlap = current_chunk[-CHUNK_OVERLAP:]

            current_chunk = overlap + "\n\n" + paragraph + "\n\n"

            # Split exceptionally long paragraphs
            while len(current_chunk) > CHUNK_SIZE:
                all_chunks.append({
                    "source": document.name,
                    "text": current_chunk[:CHUNK_SIZE].strip()
                })

                current_chunk = (
                    current_chunk[CHUNK_SIZE - CHUNK_OVERLAP:]
                )

    if current_chunk.strip():
        all_chunks.append({
            "source": document.name,
            "text": current_chunk.strip()
        })

# Save all chunks
output_file = output_folder / "knowledge_chunks.json"

with open(output_file, "w", encoding="utf-8") as file:
    json.dump(all_chunks, file, indent=4, ensure_ascii=False)

print("\nKnowledge processing completed!")
print("Total documents:", len(documents))
print("Total text chunks:", len(all_chunks))
print("Saved to:", output_file)
