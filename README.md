# Enterprise Financial Document Intelligence

Enterprise-grade Financial & Document Intelligence Engine: FastAPI backend, hybrid retrieval (BM25 + pgvector/Chroma), cross-encoder reranking, LangChain LLM pipeline, and Streamlit frontend.

This repository contains a starter scaffold for:
- FastAPI backend for document ingestion & query.
- Lightweight integration points for LangChain embeddings and vectorstores (Chroma or pgvector).
- Streamlit frontend.
- Dockerfile for containerization and docker-compose for Postgres+pgvector.

Features included in this scaffold
- Health endpoint
- File upload endpoint (multipart file ingestion)
- Lightweight indexing endpoint that extracts text from uploads and stores them in a vectorstore abstraction
- Query endpoint performing similarity search + LLM response pipeline hooks
- Streamlit frontend scaffold to interact with the API
- Dockerfile and docker-compose.yml to run Postgres with pgvector and the FastAPI app

Prerequisites
- Python 3.10+
- PostgreSQL (optional; for pgvector storage)
- Docker & docker-compose (optional; for container builds)
- OpenAI API key or other embeddings provider if you want to use cloud embeddings

Install locally

1. Clone the repo
   git clone https://github.com/dhani1110/enterprise-financial-doc-intel.git
   cd enterprise-financial-doc-intel

2. Create and activate a virtual environment
   python -m venv .venv
   source .venv/bin/activate  # macOS / Linux
   .venv\Scripts\activate     # Windows

3. Install dependencies
   pip install -r requirements.txt

4. Configure environment variables

Create a `.env` file (or set env vars directly). Typical values:

```
# .env
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://user:password@db:5432/mydb
VECTOR_STORE=chroma   # options: chroma | pgvector | memory
CHROMA_PERSIST_DIR=./chroma_db
PGVECTOR_TABLE_NAME=documents
```

- If using OPENAI embeddings, set `OPENAI_API_KEY`.
- If using `pgvector`, set `DATABASE_URL` to point at a Postgres instance with the `pgvector` extension enabled.

Run the FastAPI server (development)
   uvicorn main:app --reload --host 0.0.0.0 --port 8000

API docs are available at:
- OpenAPI: http://localhost:8000/docs
- ReDoc:   http://localhost:8000/redoc

Docker

Build the image:
```
docker build -t enterprise-financial-doc-intel:latest .
```

Run the container:
```
docker run -e OPENAI_API_KEY="$OPENAI_API_KEY" -e VECTOR_STORE=memory -p 8000:8000 enterprise-financial-doc-intel:latest
```

Or use docker-compose to run Postgres with pgvector and the app together:
```
docker-compose up --build
```

Example usage

- Health check
  GET /health

- Upload a document
  POST /upload (multipart/form-data; field `file`)

- Index document(s)
  POST /index (uses text of uploaded files or can accept raw text)

- Query
  POST /query
  JSON body:
  ```
  {
    "query": "Summarize the revenue recognition policy in the uploaded docs",
    "top_k": 5
  }
  ```

Notes & TODOs
- This scaffold uses a small in-memory DocumentStore by default and includes clear integration points for:
  - Chroma (chromadb)
  - pgvector via SQLAlchemy + pgvector type
  - LangChain LLM & reranker stages
- Add robust parsing for PDFs (pdfminer.six, tika), DOCX, PPTX, etc.
- Add tests, CI, and example notebooks to show ingestion & evaluation pipelines.

If you'd like, I can:
- Tweak the Streamlit UI layout and add example interactions.
- Add database schema examples for pgvector-backed document storage.
- Create a PR instead of committing straight to the default branch.
