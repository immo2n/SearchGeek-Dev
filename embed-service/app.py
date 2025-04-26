import chromadb
import uuid
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from typing import List

app = FastAPI()

app.mount("/static", StaticFiles(directory="front-end"), name="static")
model = SentenceTransformer("all-MiniLM-L6-v2")

chroma_client = chromadb.PersistentClient(path="./chroma_store-train")
try:
    collection = chroma_client.get_collection(name="test-products")
except:
    collection = chroma_client.create_collection(name="test-products")

class EmbedRequest(BaseModel):
    texts: List[str]

@app.get("/")
async def serve_home():
    return FileResponse(os.path.join("front-end", "index.html"))

@app.post("/embed")
async def embed(req: EmbedRequest):
    """
    vectors = model.encode(req.texts).tolist()

    ids = [str(uuid.uuid4()) for _ in req.texts]

    collection.add(
        documents=req.texts,
        embeddings=vectors,
        metadatas=[{"text": text} for text in req.texts],
        ids=ids,
    )

    print(f"Added {len(ids)} items. Total in collection: {collection.count()}")

    return {"embeddings": vectors, "ids": ids}
    """
    return {"message": "Embedding is disabled."}

class IntentData(BaseModel):
    primary_intent: str
    brand: str
    product_type: str
    desired_attributes: list
    constraints: list

@app.post("/search")
async def search(intent_data: IntentData, top_k: int = 3):
    structured_query = construct_intent_query(intent_data)

    print_r(structured_query)

    query_vector = model.encode([structured_query]).tolist()

    results = collection.query(
        query_embeddings=query_vector,
        n_results=top_k
    )

    return {
        "query": structured_query,
        "top_k": top_k,
        "results": results["documents"],
        "scores": results["distances"],
    }


def construct_intent_query(intent_data: IntentData) -> str:
    query_parts = []
    
    # Primary intent (e.g., 'Purchase')
    query_parts.append(f"Intent: {intent_data.primary_intent}")
    
    # Brand (include if mentioned, otherwise leave empty)
    if intent_data.brand:
        query_parts.append(f"Brand: {intent_data.brand}")
    else:
        query_parts.append("Brand: (none)")

    # Product type (e.g., 'Camera')
    query_parts.append(f"Product Type: {intent_data.product_type}")

    # Desired attributes (e.g., 'Professional', 'DSLR', 'Good quality')
    if intent_data.desired_attributes:
        query_parts.append(f"Attributes: {', '.join(intent_data.desired_attributes)}")
    
    # Constraints (e.g., '300$')
    if intent_data.constraints:
        query_parts.append(f"Constraints: {', '.join(intent_data.constraints)}")
    
    # Combine all parts into a structured query string
    return " ".join(query_parts)

@app.get("/count")
async def count_items():
    return {"count": collection.count()}

@app.get("/get_all")
async def get_all():
    return collection.get()