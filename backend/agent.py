import os
import sqlite3
from typing import TypedDict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from langgraph.graph import StateGraph, START, END
from langgraph.types import RetryPolicy
from langgraph.checkpoint.sqlite import SqliteSaver

from rag.retrieval_pipeline import retrieve_all

from cache import (
    get_query_embedding,
    find_cached_answer,
    save_cache
)


# --------------------------------------------------
# ENVIRONMENT
# --------------------------------------------------

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "openai/gpt-4o-mini"
)


# --------------------------------------------------
# LLM
# --------------------------------------------------

llm = ChatOpenAI(
    model=OPENROUTER_MODEL,
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
    temperature=0,
    default_headers={
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "HolidayBreakz AI Assistant",
    },
)


# --------------------------------------------------
# SYSTEM PROMPT
# --------------------------------------------------

SYSTEM_PROMPT = """
You are the HolidayBreakz customer support AI assistant.

Rules:
1. Answer only using the HolidayBreakz knowledge base.
2. Never invent or assume information.
3. If the knowledge base does not contain the answer,
   say:
   "Please contact HolidayBreakz support for the most accurate information."
4. Keep answers concise and professional.
5. Do not mention RAG, embeddings, vector database,
   LangGraph, or internal implementation details.
"""


# --------------------------------------------------
# GRAPH STATE
# --------------------------------------------------

class AgentState(TypedDict):
    user_question: str
    conversation_history: str
    topic: str
    context: str
    confidence: str
    route: str
    sources: list
    answer: str
    error: str


# --------------------------------------------------
# RETRIEVE NODE
# --------------------------------------------------

def retrieve_node(state: AgentState):
    try:
        question = state["user_question"]

        result = retrieve_all(
            question,
            k=4
        )

        return {
            "context": result["context"],
            "confidence": result["confidence"],
            "route": result["route"],
            "sources": result.get("sources", []),
            "error": "",
        }

    except Exception as e:
        return {
            "context": "",
            "confidence": "low",
            "route": "",
            "sources": [],
            "error": str(e),
        }

# --------------------------------------------------
# LLM NODE
# --------------------------------------------------

def llm_node(state: AgentState):

    context = state["context"]
    question = state["user_question"]
    sources = state.get("sources", [])

    # If retrieval failed
    if not context.strip():

        return {
            "answer": (
                "Please contact HolidayBreakz support "
                "for the most accurate information."
            )
        }

    prompt = f"""
{SYSTEM_PROMPT}

HOLIDAYBREAKZ KNOWLEDGE BASE:
{context}

CUSTOMER QUESTION:
{question}

Answer the customer based strictly on the knowledge base.

Rules for the answer:
- Do not mention internal technical details.
- Do not invent information.
- Keep the answer concise.
"""

    response = llm.invoke(prompt)

    answer = response.content.strip()

    # --------------------------------------------------
    # Add source information
    # --------------------------------------------------

    if sources:

        source_lines = []

        for source in sources:

            chunk_id = source.get(
                "chunk_id",
                "unknown"
            )

            section = source.get(
                "section",
                "General"
            )

            source_lines.append(
                f"- {section} ({chunk_id})"
            )

        answer += (
            "\n\nSources:\n"
            + "\n".join(source_lines)
        )

    return {
        "answer": answer,
        "error": ""
    }




# --------------------------------------------------
# FALLBACK NODE
# --------------------------------------------------

def fallback_node(state: AgentState):

    return {
        "answer": (
            "I'm unable to process your request right now. "
            "Please contact HolidayBreakz support for the "
            "most accurate information."
        )
    }


# --------------------------------------------------
# SQLITE CHECKPOINTER
# --------------------------------------------------

connection = sqlite3.connect(
    "holidaybreakz_checkpoints.db",
    check_same_thread=False
)

checkpointer = SqliteSaver(connection)


# --------------------------------------------------
# BUILD GRAPH
# --------------------------------------------------

builder = StateGraph(AgentState)

builder.add_node("retrieve", retrieve_node)
builder.add_node(
    "llm",
    llm_node,
    retry_policy=RetryPolicy(max_attempts=3)
)
builder.add_node("fallback", fallback_node)

builder.add_edge(START, "retrieve")

def route_after_retrieval(state: AgentState):

    if state["error"]:
        print(
            "LANGGRAPH ROUTE | fallback | retrieval error"
        )
        return "fallback"

    if state["confidence"] == "high":
        print(
            "LANGGRAPH ROUTE | llm"
        )
        return "llm"

    print(
        "LANGGRAPH ROUTE | fallback | low confidence"
    )

    return "fallback"

builder.add_edge("llm", END)
builder.add_edge("fallback", END)

# --------------------------------------------------
# COMPILE GRAPH
# --------------------------------------------------

graph = builder.compile(
    checkpointer=checkpointer
)


# --------------------------------------------------
# ASK AGENT
# --------------------------------------------------

def ask_agent(
    user_question: str,
    thread_id: str
):

     # ------------------------------------------
    # 1. Create query embedding
    # ------------------------------------------

    query_embedding = get_query_embedding(
        user_question
    )


    # ------------------------------------------
    # 2. Check semantic cache
    # ------------------------------------------

    cached_answer = find_cached_answer(
        query_embedding
    )


    # ------------------------------------------
    # 3. Return cached answer
    # ------------------------------------------

    if cached_answer:

        return cached_answer


    # ------------------------------------------
    # 4. Cache MISS → Run LangGraph
    # ------------------------------------------

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }


    result = graph.invoke(
    {
        "user_question": user_question,
       "conversation_history": "",
        "topic": "",
       "context": "",
       "confidence": "low",
       "route": "",
       "answer": "",
       "sources": [],
       "error": ""
    },
    config=config
)


    answer = result["answer"]


    # ------------------------------------------
    # 5. Save answer in cache
    # ------------------------------------------

    save_cache(
        user_question,
        query_embedding,
        answer
    )


    return answer