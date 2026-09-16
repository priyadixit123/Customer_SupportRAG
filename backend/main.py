
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent import ask_agent


app = FastAPI(
    title="HolidayBreakz OpenRouter RAG API",
    version="1.0.0"
)


# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# REQUEST / RESPONSE
# --------------------------------------------------

class ChatRequest(BaseModel):
    message: str
    session_id: str


class ChatResponse(BaseModel):
    answer: str


# --------------------------------------------------
# ROOT
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "HolidayBreakz OpenRouter RAG"
    }


# --------------------------------------------------
# HEALTH
# --------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# --------------------------------------------------
# CHAT
# --------------------------------------------------

@app.post(
    "/chat",
    response_model=ChatResponse
)
def chat(request: ChatRequest):

    try:
        answer = ask_agent(
            request.message,
            request.session_id
        )

        return {
            "answer": answer
        }

    except Exception as e:
        print("CHAT ERROR:", repr(e))
        raise e
