
# Holiday AI Customer Support Assistant

An AI-powered customer support assistant for **Holiday** built using **RAG (Retrieval-Augmented Generation), ChromaDB, LangChain, LangGraph, FastAPI, React, and OpenRouter**.

The assistant retrieves relevant information from the Holiday knowledge base before generating an answer, helping keep responses grounded in company-provided information and reducing hallucinations.

---

##  Project Overview

The Holiday AI Assistant is designed to answer customer-support questions related to:

- Holiday services
- Holiday packages
- Booking information
- Booking cancellation
- Refund information
- Customer support
- Company policies available in the knowledge base

The application uses a **RAG-based AI workflow** with LangGraph for workflow orchestration and SQLite checkpointing for session-based state persistence.

### Architecture

```text
Customer
   ↓
React Chat Interface
   ↓
FastAPI Backend
   ↓
LangGraph AI Workflow
   ↓
RAG Retriever
   ↓
ChromaDB
   ↓
Relevant Knowledge Base Chunks
   ↓
OpenRouter LLM
   ↓
Generated Answer
   ↓
Customer
```

---

#  Features

## AI Customer Support

The chatbot answers customer questions using information retrieved from the Holiday knowledge base.

## RAG Pipeline

The application uses Retrieval-Augmented Generation to retrieve relevant company information before sending context to the LLM.

This helps the assistant generate answers based on available company information instead of relying only on the model's general knowledge.

## Vector Search

Knowledge-base content is converted into embeddings and stored in **ChromaDB** for semantic similarity search.

## OpenRouter Integration

OpenRouter is used as the LLM API layer, allowing the application to work with supported AI models through a unified API.

Current model:

```text
openai/gpt-4o-mini
```

## LangGraph Workflow

LangGraph is used to organize the AI workflow into nodes and state.

Current workflow:

```text
START
  ↓
Retrieve
  ↓
LLM
  ↓
END
```

The workflow maintains structured state between nodes.

## SQLite Checkpointing

The application uses LangGraph's SQLite checkpointing mechanism to persist workflow state associated with a `thread_id`.

The frontend generates a `session_id`, which is passed to the backend and used as the LangGraph thread identifier.

```text
Frontend
   ↓
session_id
   ↓
FastAPI
   ↓
LangGraph thread_id
   ↓
SQLite Checkpointer
```

The SQLite checkpoint database is stored locally and is intentionally excluded from Git.

## FastAPI Backend

FastAPI provides REST APIs for communication between the React frontend and the AI backend.

Available endpoints:

```text
GET  /
GET  /health
POST /chat
```

## React Chat Interface

The frontend provides a travel-agent-style floating chatbot interface.

## Voice Input

The frontend supports browser-based speech recognition where supported by the browser.

## Text-to-Speech

AI responses can be spoken using the browser's speech synthesis functionality.

## Session ID

The frontend generates a session ID for each chat session.

Example:

```json
{
  "message": "What is Refund Shield?",
  "session_id": "example-session-id"
}
```

The backend maps this session ID to the LangGraph `thread_id`.

## Grounded Responses

The assistant is instructed to avoid inventing information that is not available in the HolidayBreakz knowledge base.

---

#  RAG Architecture

The RAG pipeline consists of several steps.

## Step 1 — Knowledge Base

Company information is stored in:

```text
backend/documents/knowledge_base.txt
```

---

## Step 2 — Document Loading

The knowledge base is loaded using LangChain's document loader.

---

## Step 3 — Text Chunking

The document is divided into smaller chunks.

Current configuration:

```text
chunk_size = 700
chunk_overlap = 100
```

Chunking makes the document easier to search semantically.

---

## Step 4 — Embeddings

Each text chunk is converted into a numerical vector representation using an embedding model.

Conceptually:

```text
"How can I cancel my booking?"
              ↓
       Embedding Model
              ↓
       Numerical Vector
```

---

## Step 5 — ChromaDB

The embeddings are stored in ChromaDB.

```text
ChromaDB
│
├── Chunk 1 → Vector
├── Chunk 2 → Vector
├── Chunk 3 → Vector
├── ...
└── Chunk N → Vector
```

---

## Step 6 — Retrieval

When a customer asks a question, the system searches ChromaDB for the most relevant information.

Current configuration:

```text
k = 4
```

This means the retriever attempts to return the top 4 relevant chunks.

---

## Step 7 — LLM Generation

The retrieved information is passed to the LLM through OpenRouter.

```text
HolidayBreakz Knowledge
          +
Customer Question
          ↓
        LLM
          ↓
       Answer
```

---

#  LangGraph Workflow

The AI workflow uses structured state.

Conceptually:

```text
AgentState
│
├── user_question
├── context
├── answer
└── error
```

The workflow currently contains:

```text
START
  ↓
retrieve
  ↓
llm
  ↓
END
```

The LangGraph architecture provides a foundation for adding additional agent capabilities such as:

- Retry handling
- Fallback handling
- Conditional routing
- Additional tools
- Human/supervisor review
- More complex agent workflows

---

#  Checkpointing & Session Management

The application uses SQLite-based LangGraph checkpointing.

The checkpoint database is created locally:

```text
backend/holidaybreakz_checkpoints.db
```

SQLite-related runtime files may also be created:

```text
holidaybreakz_checkpoints.db
holidaybreakz_checkpoints.db-shm
holidaybreakz_checkpoints.db-wal
```

These files are ignored by Git using:

```gitignore
*.db
*.db-shm
*.db-wal
```

The database should **not** be committed to GitHub.

---

#  Technologies Used

## Backend

- Python
- FastAPI
- Uvicorn
- LangChain
- LangGraph
- ChromaDB
- OpenRouter
- Pydantic
- SQLite

## Frontend

- React
- Vite
- JavaScript
- CSS
- Browser Speech Recognition API
- Browser Speech Synthesis API

## AI / RAG

- Retrieval-Augmented Generation
- Text Embeddings
- Vector Similarity Search
- Large Language Models
- Semantic Retrieval
- LangGraph State Management
- SQLite Checkpointing

---

#  Project Structure

```text
Customer_SupportRAG/
│
├── backend/
│   ├── documents/
│   │   └── knowledge_base.txt
│   │
│   ├── rag/
│   │   └── ingest.py
│   │
│   ├── agent.py
│   ├── main.py
│   ├── requirements.txt
│   ├── .env
│   └── chroma_db/
│
├── frontend/
│   ├── src/
│   ├── package.json
│   └── ...
│
├── .gitignore
└── README.md
```

> The SQLite checkpoint database is generated locally at runtime and is not stored in the repository.

---

#  Installation

## 1. Clone the Repository

```bash
git clone https://github.com/priyadixit123/Customer_SupportRAG.git
cd Customer_SupportRAG
```

---

#  Backend Setup

Go to the backend directory:

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

---

#  Environment Variables

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

**Never commit your real API key to GitHub.**

The following files/directories should be ignored:

```gitignore
.env
venv/
__pycache__/
chroma_db/
*.db
*.db-shm
*.db-wal
```

---

#  Build the RAG Database

From the backend directory:

```bash
python rag/ingest.py
```

The ingestion process:

```text
knowledge_base.txt
       ↓
Document Loader
       ↓
Text Splitter
       ↓
Embeddings
       ↓
ChromaDB
```

After successful ingestion, the Chroma vector database will be available in:

```text
backend/chroma_db/
```

---

#  Start the Backend

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

#  Frontend Setup

Open another terminal.

Go to:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the React development server:

```bash
npm run dev
```

Vite will provide a local URL, normally similar to:

```text
http://localhost:5173/
```

Open the URL in your browser.

---

#  API Flow

The frontend sends a request to:

```text
POST /chat
```

### Example Request

```json
{
  "message": "How can I cancel my HolidayBreakz booking?",
  "session_id": "example-session-id"
}
```

### Example Response

```json
{
  "answer": "AI-generated answer based on the Holiday knowledge base."
}
```

---

#  Complete Request Flow

```text
User asks a question
        ↓
React Frontend
        ↓
POST /chat
        ↓
FastAPI
        ↓
session_id
        ↓
LangGraph thread_id
        ↓
Retrieve relevant documents
        ↓
ChromaDB
        ↓
Knowledge Base Context
        ↓
OpenRouter LLM
        ↓
Generated Answer
        ↓
FastAPI Response
        ↓
React Chat Interface
```

---

#  Security Notes

- Never commit `.env`
- Never expose the OpenRouter API key in the React frontend
- Never commit the ChromaDB directory
- Never commit SQLite checkpoint databases
- Keep API credentials in environment variables

---

#  Future Improvements

Planned improvements include:

- Retry policies for failed AI/tool calls
- Conditional fallback handling
- More advanced LangGraph routing
- Additional external tools/APIs
- Supervisor/manager agent
- Human-in-the-loop workflows
- Better conversational memory
- Persistent production database
- Authentication and authorization
- Production deployment
- Monitoring and logging

---

#  Project Purpose

This project demonstrates practical implementation of:

```text
RAG
+
Vector Database
+
LLM
+
LangGraph
+
FastAPI
+
React
+
Session Management
+
SQLite Checkpointing
```

