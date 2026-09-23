# Holiday AI Customer Support RAG Agent

An AI-powered customer support assistant for **HolidayBreakz** built using **RAG (Retrieval-Augmented Generation), Hybrid Search, BM25, ChromaDB, LangChain, LangGraph, FastAPI, React, OpenRouter, and caching**.

The assistant retrieves relevant information from the HolidayBreakz knowledge base using both **semantic vector search and keyword-based BM25 retrieval**, combines the results using **Reciprocal Rank Fusion (RRF)**, and then provides the retrieved context to an LLM for grounded response generation.

A caching layer is also used to reduce repeated retrieval/LLM work for frequently repeated queries.

---

# Project Overview

The Holiday AI Assistant is designed to answer customer-support questions related to:

- HolidayBreakz services
- Holiday packages
- Booking information
- Booking cancellation
- Refund information
- Seat selection
- Baggage
- Meals and other ancillaries
- Customer support
- Company policies available in the knowledge base

The application uses a **Hybrid RAG architecture** combining:

```text
Vector Search
      +
BM25 Keyword Search
      ↓
RRF Hybrid Ranking
      ↓
Relevant Context
      ↓
LLM
      ↓
Grounded Answer
```

LangGraph is used to orchestrate the AI workflow, while SQLite checkpointing provides session-based workflow persistence.

---

# Architecture

## Current Architecture

```text
                         Customer
                            │
                            ▼
                    React Chat Interface
                            │
                            ▼
                       FastAPI API
                            │
                            ▼
                       LangGraph
                            │
                            ▼
                         Query
                            │
                            ▼
                         Cache
                     ┌──────┴──────┐
                     │             │
                 Cache Hit      Cache Miss
                     │             │
                     │             ▼
                     │       Hybrid Retrieval
                     │             │
                     │       ┌─────┴─────┐
                     │       │           │
                     │       ▼           ▼
                     │    Chroma       BM25
                     │   Vector       Keyword
                     │   Search       Search
                     │       │           │
                     │       └─────┬─────┘
                     │             ▼
                     │            RRF
                     │             │
                     │             ▼
                     │        Top K Chunks
                     │             │
                     │             ▼
                     │          OpenRouter
                     │             │
                     │             ▼
                     │        Generated Answer
                     │             │
                     └─────────────┤
                                   ▼
                           React Chat Interface
```

---

# Key Features

## 1. AI Customer Support

The chatbot answers customer questions using information retrieved from the HolidayBreakz knowledge base.

The assistant is instructed to avoid inventing company-specific information that is not available in the knowledge base.

---

# 2. Retrieval-Augmented Generation

The application uses Retrieval-Augmented Generation instead of sending the user question directly to the LLM.

The process is:

```text
User Question
      ↓
Retrieve Relevant Knowledge
      ↓
Build Context
      ↓
Send Context + Question to LLM
      ↓
Generate Answer
```

This helps ground responses in company-provided information.

---

# 3. Hybrid Retrieval

The project uses two retrieval strategies:

```text
                    User Query
                        │
              ┌─────────┴─────────┐
              ▼                   ▼
        Vector Search           BM25
        Semantic Search       Keyword Search
              │                   │
              └─────────┬─────────┘
                        ▼
                       RRF
                        │
                        ▼
                  Hybrid Results
```

This allows the system to benefit from both:

### Semantic Search

ChromaDB can retrieve documents based on the meaning of a question.

For example:

```text
User:
"When will I receive my money after cancellation?"
```

The vector retriever can understand that the question is related to:

```text
refund processing time
```

### BM25 Search

BM25 focuses on keyword overlap.

For example:

```text
refund
cancellation
7 days
10 days
```

This can be useful when the user's query contains important exact terms.

---

# 4. BM25 Retrieval

BM25 is implemented using the `rank-bm25` Python package.

BM25 is a **lexical retrieval algorithm**, not an embedding model.

The implementation tokenizes the knowledge-base chunks and calculates keyword-based relevance scores.

Example:

```python
from rank_bm25 import BM25Okapi
```

The same knowledge-base chunks used by the vector system are also used to build the BM25 index.

---

# 5. Reciprocal Rank Fusion (RRF)

The project combines vector-search results and BM25 results using **Reciprocal Rank Fusion**.

Instead of directly adding Chroma similarity scores and BM25 scores, RRF combines the **ranking positions**.

The basic formula is:

```text
RRF Score = 1 / (k + rank)
```

where:

```text
k = 60
```

Example:

```text
Vector Search:

1. Chunk A
2. Chunk B
3. Chunk C


BM25:

1. Chunk C
2. Chunk A
3. Chunk D
```

The documents appearing highly in both rankings receive a stronger combined RRF score.

The final ranking becomes:

```text
Vector Results
      +
BM25 Results
      ↓
RRF Fusion
      ↓
Final Ranked Documents
```

---

# 6. Stable Chunk IDs

Each knowledge-base chunk receives a stable identifier during ingestion.

Example:

```text
kb_000
kb_001
kb_002
kb_003
...
```

These IDs are stored in document metadata.

Example:

```python
chunk.metadata["chunk_id"] = f"kb_{index:03d}"
```

Stable chunk IDs are useful for:

- Hybrid retrieval
- RRF ranking
- Retrieval evaluation
- Recall@K
- Precision@K
- MRR
- Debugging
- Comparing retrieval strategies

---

# 7. Query Caching

The project includes a caching layer to avoid repeating expensive processing for identical or repeated queries.

Conceptually:

```text
User Query
    ↓
Normalize Query
    ↓
Check Cache
    │
    ├── Cache Hit
    │      ↓
    │   Return Cached Result
    │
    └── Cache Miss
           ↓
      Hybrid Retrieval
           ↓
           LLM
           ↓
      Store Result
           ↓
      Return Answer
```

Caching can help reduce:

- Repeated retrieval operations
- Repeated LLM calls
- API usage
- Response latency for repeated queries

A production implementation can use a persistent cache such as Redis, while a local development implementation can use an in-memory or file-based cache.

---

# 8. Vector Search

Knowledge-base content is converted into embeddings and stored in **ChromaDB**.

Current embedding model:

```text
text-embedding-3-small
```

The embedding API is accessed through OpenRouter's compatible API endpoint.

Conceptually:

```text
Knowledge Base
      ↓
Text Chunk
      ↓
Embedding Model
      ↓
Numerical Vector
      ↓
ChromaDB
```

---

# 9. Retrieval Configuration

Current chunking configuration:

```text
chunk_size = 700
chunk_overlap = 100
```

Current retrieval configuration:

```text
top_k = 4
```

The hybrid retriever retrieves results from:

```text
Chroma
+
BM25
```

and then applies RRF to produce the final ranked documents.

---

# RAG Pipeline

## Step 1 — Knowledge Base

Company information is stored in:

```text
backend/documents/knowledge_base.txt
```

---

## Step 2 — Document Loading

The knowledge base is loaded using a LangChain document loader.

---

## Step 3 — Text Chunking

The document is divided into smaller chunks using:

```text
RecursiveCharacterTextSplitter
```

Configuration:

```text
chunk_size = 700
chunk_overlap = 100
```

---

## Step 4 — Chunk IDs

Each chunk receives a stable ID:

```text
kb_000
kb_001
kb_002
...
```

---

## Step 5 — Embeddings

Each chunk is converted into an embedding vector.

```text
Text
 ↓
Embedding Model
 ↓
Vector
```

---

## Step 6 — ChromaDB

The vectors are stored in ChromaDB.

```text
ChromaDB
│
├── kb_000 → Vector
├── kb_001 → Vector
├── kb_002 → Vector
├── ...
└── kb_041 → Vector
```

---

## Step 7 — BM25 Index

The same text chunks are indexed using BM25.

```text
Knowledge Base Chunks
        ↓
Tokenization
        ↓
BM25 Index
```

---

## Step 8 — Hybrid Retrieval

When the user asks a question:

```text
Question
   │
   ├───────────────┐
   ▼               ▼
Chroma            BM25
Vector Search     Keyword Search
   │               │
   └───────┬───────┘
           ▼
          RRF
           ▼
       Top K Chunks
```

---

## Step 9 — Context Construction

The selected chunks are combined into context.

```text
Chunk 1
   +
Chunk 2
   +
Chunk 3
   +
Chunk 4
   ↓
Context
```

---

## Step 10 — LLM Generation

The retrieved context and customer question are passed to the LLM.

```text
Customer Question
        +
Retrieved Context
        ↓
      OpenRouter
        ↓
      LLM Answer
```

---

# LangGraph Workflow

LangGraph is used to organize the AI workflow into structured nodes and state.

Current conceptual workflow:

```text
START
  ↓
Retrieve
  ↓
LLM
  ↓
END
```

The retrieval node now conceptually performs:

```text
Query
 ↓
Cache Check
 ↓
Hybrid Retrieval
 ↓
RRF
 ↓
Context
```

The workflow can later be expanded with:

- Retry handling
- Fallback retrieval
- Conditional routing
- Tool calling
- Human-in-the-loop review
- Supervisor agents
- External APIs
- Validation nodes

---

# Agent State

The LangGraph state can contain information such as:

```text
AgentState
│
├── user_question
├── context
├── answer
├── session_id
└── error
```

This structured state allows additional nodes to be added without redesigning the complete application.

---

# Retrieval Evaluation

The project can evaluate retrieval quality using standard Information Retrieval metrics.

The main metrics are:

## Recall@K

Measures how many of the relevant chunks were retrieved.

```text
Recall@K =
Relevant Retrieved Documents
-----------------------------
Total Relevant Documents
```

Example:

```text
Relevant chunks:
kb_001
kb_007

Retrieved Top 4:
kb_001
kb_003
kb_007
kb_010
```

Then:

```text
Recall@4 = 2 / 2 = 1.0
```

---

## Precision@K

Measures how many retrieved documents are actually relevant.

```text
Precision@K =
Relevant Retrieved Documents
-----------------------------
K
```

For example:

```text
2 relevant documents
4 retrieved documents

Precision@4 = 2 / 4 = 0.5
```

---

## Hit Rate@K

Measures whether at least one relevant document appears in the top K results.

```text
Hit Rate@K =
1 if at least one relevant chunk is retrieved
0 otherwise
```

---

## MRR

Mean Reciprocal Rank measures how high the first relevant document appears.

Example:

```text
Rank 1 → 1/1 = 1.0
Rank 2 → 1/2 = 0.5
Rank 3 → 1/3 = 0.333
```

For multiple questions, the reciprocal ranks can be averaged.

---

# Retrieval Evaluation Dataset

A manually labeled evaluation dataset can be created for representative customer questions.

Example:

```json
[
  {
    "question": "What is the refund policy?",
    "relevant_chunk_ids": [
      "kb_007",
      "kb_012"
    ]
  },
  {
    "question": "How long does a refund take?",
    "relevant_chunk_ids": [
      "kb_012"
    ]
  }
]
```

The same evaluation dataset can be used to compare:

```text
Vector Search
      vs
BM25
      vs
Hybrid + RRF
```

Example evaluation table:

| Retriever | Recall@4 | Precision@4 | Hit Rate@4 | MRR |
|---|---:|---:|---:|---:|
| Vector | - | - | - | - |
| BM25 | - | - | - | - |
| Hybrid RRF | - | - | - | - |

The purpose of this evaluation is to measure whether combining retrieval methods improves retrieval performance on the project's evaluation dataset.

---

# SQLite Checkpointing

The application uses LangGraph's SQLite checkpointing mechanism to persist workflow state.

The local checkpoint database is:

```text
backend/holidaybreakz_checkpoints.db
```

SQLite runtime files may include:

```text
holidaybreakz_checkpoints.db
holidaybreakz_checkpoints.db-shm
holidaybreakz_checkpoints.db-wal
```

These files are excluded from Git.

---

# Session Management

The frontend generates a session ID.

Example:

```json
{
  "message": "What is Refund Shield?",
  "session_id": "example-session-id"
}
```

The backend maps the session ID to the LangGraph thread ID.

```text
React
  ↓
session_id
  ↓
FastAPI
  ↓
thread_id
  ↓
LangGraph
  ↓
SQLite Checkpointer
```

This allows workflow state to persist across messages within a session.

---

# FastAPI Backend

FastAPI provides communication between the React frontend and AI backend.

Available endpoints:

```text
GET  /
GET  /health
POST /chat
```

---

# React Frontend

The frontend is built using:

- React
- Vite
- JavaScript
- CSS

The interface provides a travel-agent-style floating customer-support chatbot.

Features include:

- Chat interface
- Session ID generation
- Quick actions
- Voice input
- Text-to-speech
- Typing/response effects
- API integration with FastAPI

---

# Voice Input

Browser Speech Recognition is used where supported.

Conceptually:

```text
User Speech
    ↓
Browser Speech Recognition
    ↓
Text
    ↓
FastAPI
    ↓
AI Assistant
```

---

# Text-to-Speech

AI responses can be spoken using the browser's Speech Synthesis API.

```text
AI Response
    ↓
Browser Speech Synthesis
    ↓
Spoken Response
```

---

# API Flow

The frontend sends requests to:

```text
POST /chat
```

Example request:

```json
{
  "message": "How can I cancel my HolidayBreakz booking?",
  "session_id": "example-session-id"
}
```

Example response:

```json
{
  "answer": "AI-generated answer based on the HolidayBreakz knowledge base."
}
```

---

# Complete Request Flow

```text
User Question
      ↓
React Frontend
      ↓
POST /chat
      ↓
FastAPI
      ↓
LangGraph
      ↓
Cache Check
      │
      ├── Hit ───────────────┐
      │                      │
      └── Miss                │
            ↓                │
       Hybrid Retrieval      │
            ↓                │
      ┌─────┴─────┐          │
      ↓           ↓          │
   Chroma        BM25        │
   Vector       Keyword      │
      ↓           ↓          │
      └─────┬─────┘          │
            ↓                │
           RRF               │
            ↓                │
       Top K Chunks          │
            ↓                │
       OpenRouter LLM        │
            ↓                │
        Cache Result ────────┘
            ↓
       Final Answer
            ↓
      React Interface
```

---

# Project Structure

```text
Customer_SupportRAG/
│
├── backend/
│   │
│   ├── documents/
│   │   └── knowledge_base.txt
│   │
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── ingest.py
│   │   ├── retriever.py
│   │   ├── bm25_retriever.py
│   │   └── hybrid_retriever.py
│   │
│   ├── evaluation/
│   │   └── eval_dataset.json
│   │
│   ├── cache.py
│   ├── agent.py
│   ├── main.py
│   ├── requirements.txt
│   ├── .env
│   ├── chroma_db/
│   └── holidaybreakz_checkpoints.db
│
├── frontend/
│   ├── src/
│   ├── package.json
│   └── ...
│
├── .gitignore
└── README.md
```

---

# Installation

## 1. Clone Repository

```bash
git clone https://github.com/priyadixit123/Customer_SupportRAG.git
cd Customer_SupportRAG
```

---

# Backend Setup

Go to the backend:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

For BM25 support:

```bash
pip install rank-bm25
```

---

# Important Python Packages

The project uses:

```text
fastapi
uvicorn
langchain
langchain-community
langchain-openai
langchain-chroma
langchain-text-splitters
chromadb
rank-bm25
python-dotenv
langgraph
```

---

# Environment Variables

Create:

```text
backend/.env
```

Add:

```env
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=openai/gpt-4o-mini
CHROMA_PATH=./chroma_db
```

Never commit your real API key.

---

# Build the RAG Database

From the backend directory:

```bash
python -m rag.ingest
```

The ingestion pipeline is:

```text
knowledge_base.txt
       ↓
Document Loader
       ↓
Text Splitter
       ↓
Stable Chunk IDs
       ↓
Embeddings
       ↓
ChromaDB
```

The same chunks are subsequently used for BM25 retrieval.

---

# Test Hybrid Retrieval

From the backend directory:

```bash
python -m rag.retriever
```

The test performs:

```text
User Query
     ↓
Vector Search
     +
BM25 Search
     ↓
RRF
     ↓
Top K Results
```

Example query:

```text
What is the refund policy?
```

The output can include:

```text
Rank: 1
Chunk ID: kb_007
RRF Score: ...

Rank: 2
Chunk ID: kb_012
RRF Score: ...

Rank: 3
Chunk ID: kb_003
RRF Score: ...
```

---

# Start Backend

From:

```text
backend/
```

Run:

```bash
uvicorn main:app --reload --port 8000
```

Backend:

```text
http://127.0.0.1:8000
```

FastAPI documentation:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/health
```

---

# Frontend Setup

Open another terminal.

Go to:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start Vite:

```bash
npm run dev
```

The frontend will normally be available at:

```text
http://localhost:5173/
```

---

# Security

The project follows these security practices:

- API keys are stored in environment variables
- `.env` is excluded from Git
- OpenRouter credentials are never exposed to React
- ChromaDB is generated locally
- SQLite checkpoint databases are not committed
- Virtual environments are excluded from Git

Recommended `.gitignore`:

```gitignore
.env
venv/
__pycache__/
*.pyc

chroma_db/

*.db
*.db-shm
*.db-wal

node_modules/
dist/


ll@K, Precision@K, Hit Rate and MRR
