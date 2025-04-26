import chromadb
from sentence_transformers import SentenceTransformer
import json

# Initialize ChromaDB client
chroma_client = chromadb.PersistentClient(path="./chroma_store-train")
try:
    collection = chroma_client.get_collection(name="test-products")
except:
    collection = chroma_client.create_collection(name="test-products")

# Initialize SentenceTransformer model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Counter for processed lines
line_count = 0

# Function to ensure metadata values are valid types (str, int, float, or bool)
def ensure_valid_metadata(metadata):
    return {key: (str(value) if value is not None else "") for key, value in metadata.items()}

# Open the JSON file and process all lines
with open("train-data.json", "r", encoding="utf-8") as f:
    for line in f:
        item = json.loads(line)

        def clean_text(text):
            return text.strip(' "@en-US') if text else ""

        # LEFT product
        title_left = clean_text(item.get("title_left"))
        description_left = clean_text(item.get("description_left"))
        text_left = f"{title_left} {description_left}"

        metadata_left = {
            "side": "left",
            "pair_id": item["pair_id"],
            "category": item.get("category_left"),
            "brand": item.get("brand_left"),
            "title": title_left,
            "description": description_left,
        }

        # Ensure all metadata values are of valid type
        metadata_left = ensure_valid_metadata(metadata_left)

        # Get embedding for left product
        vector_left = model.encode(text_left).tolist()

        # RIGHT product
        title_right = clean_text(item.get("title_right"))
        description_right = clean_text(item.get("description_right"))
        text_right = f"{title_right} {description_right}"

        metadata_right = {
            "side": "right",
            "pair_id": item["pair_id"],
            "category": item.get("category_right"),
            "brand": item.get("brand_right"),
            "title": title_right,
            "description": description_right,
        }

        # Ensure all metadata values are of valid type
        metadata_right = ensure_valid_metadata(metadata_right)

        # Get embedding for right product
        vector_right = model.encode(text_right).tolist()

        # Add documents (text) and embeddings to ChromaDB collection
        collection.add(
            documents=[text_left, text_right],
            embeddings=[vector_left, vector_right],
            metadatas=[metadata_left, metadata_right],
            ids=[f"{item['pair_id']}_left", f"{item['pair_id']}_right"]
        )

        # Update line count and print status
        line_count += 1
        print(f"Processed line {line_count} (Pair ID: {item['pair_id']})")

print(f"\nTotal lines processed: {line_count}")
