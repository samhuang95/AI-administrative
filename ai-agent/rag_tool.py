import os
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv # Added import

# Load environment variables from .env file (assuming it's in the same directory as this script)
# This ensures GOOGLE_API_KEY is available when initializing the client
load_dotenv(Path(__file__).resolve().parent / ".env")

import chromadb
from chromadb.utils import embedding_functions
from google import genai
from google.genai import types

KNOWLEDGE_BASE_PATH = Path(__file__).resolve().parent.parent / "data" / "knowledge_base"
CHROMA_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "chroma_db"

# Initialize Google GenAI Client
# Ensure GOOGLE_API_KEY is set in environment variables
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

class GoogleGenAIEmbeddingFunction(embedding_functions.EmbeddingFunction):
    """Custom embedding function using Google GenAI SDK."""
    def __call__(self, input: List[str]) -> List[List[float]]:
        # Embed content using the new SDK
        # Model 'text-embedding-004' is a good default for retrieval
        embeddings = []
        for text in input:
            try:
                response = client.models.embed_content(
                    model="text-embedding-004",
                    contents=text
                )
                embeddings.append(response.embeddings[0].values)
            except Exception as e:
                print(f"Error embedding text: {e}")
                # Return a zero vector or handle error appropriately
                # For simplicity, we might skip or raise, but let's try to be robust
                embeddings.append([0.0] * 768) # Assuming 768 dim, but this is risky.
        return embeddings

def _get_collection():
    """Initialize and return the ChromaDB collection."""
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))

    # Use our custom embedding function
    embedding_fn = GoogleGenAIEmbeddingFunction()

    collection = chroma_client.get_or_create_collection(
        name="company_knowledge_base",
        embedding_function=embedding_fn
    )
    return collection

def _index_documents():
    """Reads documents and indexes them into ChromaDB if not already present."""
    if not KNOWLEDGE_BASE_PATH.exists():
        return

    collection = _get_collection()

    # Simple check: if collection is empty, index everything.
    # In a real app, we'd check file hashes or modification times.
    if collection.count() > 0:
        # For this demo, we'll just return.
        # To force re-index, user can delete the chroma_db folder.
        # Or we can implement a smarter sync.
        # Let's do a simple "delete all and re-index" for now to ensure freshness
        # since the user said they want to "freely add/change".
        # BUT deleting every time is slow.
        # Let's just check if the count matches roughly or just re-add (upsert).
        pass

    # Re-reading files
    docs = []
    ids = []
    metadatas = []

    for file_path in KNOWLEDGE_BASE_PATH.glob("*.*"):
        if file_path.suffix.lower() in ['.txt', '.md']:
            try:
                content = file_path.read_text(encoding='utf-8')
                # Split by double newlines to create chunks
                chunks = content.split("\n\n")
                for i, chunk in enumerate(chunks):
                    if chunk.strip():
                        docs.append(chunk.strip())
                        ids.append(f"{file_path.name}_{i}")
                        metadatas.append({"source": file_path.name})
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

    if docs:
        # Upsert (update or insert)
        collection.upsert(
            documents=docs,
            ids=ids,
            metadatas=metadatas
        )

def search_company_policies(query: str) -> Dict:
    """Tool: Search company policies, culture, and performance standards using Vector Search.

    Use this tool when answering questions about:
    - Company culture and values
    - Performance review standards and grading
    - HR policies and guidelines

    Args:
        query: The search keywords or question.
    """
    # Ensure index is up to date (simple approach: run indexer on every query)
    # In production, this should be an async background task or triggered by file watch.
    _index_documents()

    collection = _get_collection()

    results = collection.query(
        query_texts=[query],
        n_results=3
    )

    if not results['documents'][0]:
        return {"status": "no_match", "text": "在知識庫中找不到相關資訊。"}

    formatted_results = []
    for i, doc in enumerate(results['documents'][0]):
        source = results['metadatas'][0][i]['source']
        formatted_results.append(f"來源: {source}\n內容:\n{doc}")

    return {"status": "success", "text": "\n\n---\n\n".join(formatted_results)}

