"""
Minimal FastAPI scaffold for Enterprise Financial Document Intelligence.

Capabilities:
- /health
- /upload  (uploads a file, extracts text)
- /index   (index stored documents into vectorstore)
- /query   (run a retrieval->LLM pipeline; placeholder LLM integration)

This file is intentionally light and contains clear integration points for:
- LangChain embeddings
- Chroma or pgvector vectorstores
- Cross-encoder reranking and LLM response generation
"""

import os
import uuid
import tempfile
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

# Config
VECTOR_STORE = os.getenv("VECTOR_STORE", "memory")  # options: chroma | pgvector | memory
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
DATABASE_URL = os.getenv("DATABASE_URL")  # for pgvector
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Optional imports (lazy)
try:
    from langchain.embeddings import OpenAIEmbeddings
    from langchain.schema import Document
except Exception:
    OpenAIEmbeddings = None
    Document = None

# Minimal in-memory store used by default
class InMemoryStore:
    def __init__(self):
        # Each entry: {"id": str, "text": str, "metadata": {} , "vector": list|None}
        self._docs = []

    def add_documents(self, docs: List[dict]):
        for d in docs:
            d_id = d.get("id") or str(uuid.uuid4())
            self._docs.append({"id": d_id, "text": d["text"], "metadata": d.get("metadata", {}), "vector": d.get("vector")})

    def get_all_texts(self):
        return [d["text"] for d in self._docs]

    def simple_keyword_search(self, query: str, top_k: int = 5):
        # very naive lexical scoring: count of query words in doc
        q_words = set(query.lower().split())
        scored = []
        for d in self._docs:
            words = set(d["text"].lower().split())
            score = len(q_words & words)
            scored.append((score, d))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [s[1] for s in scored[:top_k]]

    def similarity_search(self, embedding: List[float], top_k: int = 5):
        # naive cosine similarity over stored vectors (if present)
        import math
        scored = []
        for d in self._docs:
            v = d.get("vector")
            if not v:
                continue
            # cosine
            dot = sum(a*b for a, b in zip(v, embedding))
            norm_a = math.sqrt(sum(a*a for a in v))
            norm_b = math.sqrt(sum(b*b for b in embedding))
            if norm_a == 0 or norm_b == 0:
                score = 0.0
            else:
                score = dot / (norm_a * norm_b)
            scored.append((score, d))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [s[1] for s in scored[:top_k]]


# Instantiate chosen store (for this scaffold, only memory is fully wired)
if VECTOR_STORE == "memory" or VECTOR_STORE not in ("chroma", "pgvector"):
    store = InMemoryStore()
else:
    # Placeholders for future Chroma/pgvector integration
    store = InMemoryStore()


app = FastAPI(title="Enterprise Financial Document Intelligence")


class QueryIn(BaseModel):
    query: str
    top_k: Optional[int] = 5


@app.get("/health")
def health():
    return {"status": "ok", "vector_store": VECTOR_STORE}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a document. The API saves the uploaded file to a temp directory and extracts text.
    This is intentionally minimal; for production use, extract text using proper parsers
    for PDF/DOCX (pdfminer, tika, docx) and handle encoding and security.
    """
    suffix = os.path.splitext(file.filename)[1].lower()
    contents = await file.read()
    text = None

    if suffix in (".txt", ".md"):
        text = contents.decode("utf-8", errors="ignore")
    elif suffix in (".pdf",):
        # Placeholder: In production, use robust PDF extraction (pdfminer.six or tika)
        # Save file and return path for async processing
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        tmp.write(contents)
        tmp.close()
        return {"status": "uploaded", "filename": file.filename, "tmp_path": tmp.name, "note": "PDF saved. Extract text using a PDF parser in a background job."}
    else:
        # Generic fallback
        try:
            text = contents.decode("utf-8", errors="ignore")
        except Exception:
            raise HTTPException(status_code=400, detail="Unsupported file type and could not decode file.")

    # For the scaffold, store the raw text in the in-memory store
    doc = {"id": str(uuid.uuid4()), "text": text, "metadata": {"filename": file.filename}}
    store.add_documents([doc])
    return {"status": "ok", "id": doc["id"], "filename": file.filename}


@app.post("/index")
async def index_texts():
    """
    Index existing texts in the store by computing embeddings and (optionally) persisting them to vectorstore.
    For this scaffold we compute embeddings using OpenAI (if configured) and attach them in-memory.
    """
    if OpenAIEmbeddings is None:
        return JSONResponse(status_code=500, content={"error": "langchain or embeddings not installed in this environment."})

    if not OPENAI_API_KEY:
        return JSONResponse(status_code=400, content={"error": "OPENAI_API_KEY not set. Set it to compute embeddings or use a different embeddings provider."})

    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    texts = store.get_all_texts()
    if not texts:
        return {"status": "no_documents"}

    # compute embeddings in batches
    batch_size = 16
    all_vectors = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        vs = embeddings.embed_documents(batch)
        all_vectors.extend(vs)

    # attach vectors to store documents (in-memory)
    # NOTE: This assumes the order of store.get_all_texts() corresponds to stored docs order
    # In production, work with explicit ids.
    for idx, vec in enumerate(all_vectors):
        try:
            store._docs[idx]["vector"] = vec
        except IndexError:
            continue

    return {"status": "indexed", "num_documents": len(all_vectors)}


@app.post("/query")
async def query(q: QueryIn):
    """
    Query endpoint that demonstrates hybrid retrieval:
     - Compute embedding for the query
     - Use vector similarity (if vectors present)
     - Use a naive keyword search (as BM25 placeholder)
     - Merge results and return candidate contexts

    For final answer generation, plug in your LLM (LangChain chain) and reranker here.
    """
    if not q.query:
        raise HTTPException(status_code=400, detail="No query provided")

    # Attempt embedding-based retrieval if embeddings are available
    embedding = None
    use_embedding = False
    if OpenAIEmbeddings is not None and OPENAI_API_KEY:
        try:
            emb = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
            embedding = emb.embed_query(q.query)
            use_embedding = True
        except Exception:
            use_embedding = False

    vector_results = []
    if use_embedding:
        vector_results = store.similarity_search(embedding, top_k=q.top_k)

    keyword_results = store.simple_keyword_search(q.query, top_k=q.top_k)

    # Merge results (simple dedupe, prefer vector results)
    seen_ids = set()
    merged = []
    for doc in vector_results + keyword_results:
        if doc["id"] in seen_ids:
            continue
        seen_ids.add(doc["id"])
        merged.append({"id": doc["id"], "text": doc["text"][:1000], "metadata": doc.get("metadata", {})})

    # Placeholder: call a LangChain LLM chain here to generate the final answer using `merged` as context
    answer = {
        "answer": "This is a placeholder answer. Plug in your LLM/chain to generate a real response from retrieved contexts.",
        "candidates": merged,
    }

    return answer


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
