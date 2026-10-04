
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


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "openai/gpt-4o-mini"
)

if not OPENROUTER_API_KEY:
    raise ValueError(
        "OPENROUTER_API_KEY is missing in .env"
    )


# =========================================================
# LLM
# =========================================================

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


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are the HolidayBreakz customer support AI assistant.

Rules:

1. Answer only using the HolidayBreakz knowledge base.
2. Never invent or assume information.
3. If the knowledge base does not contain the answer,
   say:

   "Please contact HolidayBreakz support for the most accurate information."

4. Keep answers concise and professional.
5. Do not mention:
   - RAG
   - embeddings
   - vector database
   - LangGraph
   - BM25
   - reranking
   - Neo4j
   - internal implementation details
"""


# =========================================================
# LANGGRAPH STATE
# =========================================================

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


# =========================================================
# RETRIEVAL NODE
# =========================================================

def retrieve_node(state: AgentState):

    question = state["user_question"]

    print("\n")
    print("=" * 60)
    print("LANGGRAPH RETRIEVE NODE")
    print("=" * 60)

    print(
        "USER QUESTION |",
        question
    )

    try:

        result = retrieve_all(
            question,
            k=4
        )

        context = result.get(
            "context",
            ""
        )

        confidence = result.get(
            "confidence",
            "low"
        )

        route = result.get(
            "route",
            ""
        )

        sources = result.get(
            "sources",
            []
        )

        print(
            "RETRIEVED SOURCES |",
            sources
        )

        print(
            "RETRIEVED CONFIDENCE |",
            confidence
        )

        print(
            "RETRIEVED ROUTE |",
            route
        )

        return {
            "context": context,
            "confidence": confidence,
            "route": route,
            "sources": sources,
            "error": ""
        }

    except Exception as e:

        print(
            "RETRIEVAL ERROR |",
            repr(e)
        )

        return {
            "context": "",
            "confidence": "low",
            "route": "",
            "sources": [],
            "error": str(e)
        }


# =========================================================
# ROUTE AFTER RETRIEVAL
# =========================================================

def route_after_retrieval(
    state: AgentState
):

    error = state.get(
        "error",
        ""
    )

    confidence = state.get(
        "confidence",
        "low"
    )

    sources = state.get(
        "sources",
        []
    )

    print(
        "ROUTER SOURCES |",
        sources
    )

    if error:

        print(
            "LANGGRAPH ROUTE | fallback | retrieval error"
        )

        return "fallback"

    if confidence == "high":

        print(
            "LANGGRAPH ROUTE | llm"
        )

        return "llm"

    print(
        "LANGGRAPH ROUTE | fallback | low confidence"
    )

    return "fallback"


# =========================================================
# LLM NODE
# =========================================================

def llm_node(state: AgentState):

    context = state.get(
        "context",
        ""
    )

    question = state.get(
        "user_question",
        ""
    )

    sources = state.get(
        "sources",
        []
    )

    print(
        "LLM NODE SOURCES |",
        sources
    )

    # -----------------------------------------------------
    # No context
    # -----------------------------------------------------

    if not context.strip():

        return {
            "answer": (
                "Please contact HolidayBreakz support "
                "for the most accurate information."
            ),
            "error": ""
        }

    # -----------------------------------------------------
    # LLM PROMPT
    # -----------------------------------------------------

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
- Do not add information that is not present
  in the knowledge base.
- Keep the answer concise.
"""

    try:

        response = llm.invoke(
            prompt
        )

        answer = response.content.strip()

        print(
            "LLM ANSWER GENERATED"
        )

        return {
            "answer": answer,
            "error": ""
        }

    except Exception as e:

        print(
            "LLM ERROR |",
            repr(e)
        )

        return {
            "answer": (
                "Please contact HolidayBreakz support "
                "for the most accurate information."
            ),
            "error": str(e)
        }


# =========================================================
# FALLBACK NODE
# =========================================================

def fallback_node(state: AgentState):

    sources = state.get(
        "sources",
        []
    )

    print(
        "FALLBACK NODE SOURCES |",
        sources
    )

    return {
        "answer": (
            "Please contact HolidayBreakz support "
            "for the most accurate information."
        ),
        "error": ""
    }


# =========================================================
# SQLITE CHECKPOINTER
# =========================================================

connection = sqlite3.connect(
    "holidaybreakz_checkpoints.db",
    check_same_thread=False
)

checkpointer = SqliteSaver(
    connection
)


# =========================================================
# BUILD LANGGRAPH
# =========================================================

builder = StateGraph(
    AgentState
)


# ---------------------------------------------------------
# Nodes
# ---------------------------------------------------------

builder.add_node(
    "retrieve",
    retrieve_node
)

builder.add_node(
    "llm",
    llm_node,
    retry_policy=RetryPolicy(
        max_attempts=3
    )
)

builder.add_node(
    "fallback",
    fallback_node
)


# ---------------------------------------------------------
# START
# ---------------------------------------------------------

builder.add_edge(
    START,
    "retrieve"
)


# ---------------------------------------------------------
# Retrieval → LLM / Fallback
# ---------------------------------------------------------

builder.add_conditional_edges(
    "retrieve",
    route_after_retrieval,
    {
        "llm": "llm",
        "fallback": "fallback"
    }
)


# ---------------------------------------------------------
# END
# ---------------------------------------------------------

builder.add_edge(
    "llm",
    END
)

builder.add_edge(
    "fallback",
    END
)


# =========================================================
# COMPILE
# =========================================================

graph = builder.compile(
    checkpointer=checkpointer
)


# =========================================================
# ASK AGENT
# =========================================================

def ask_agent(
    user_question: str,
    thread_id: str
):

    print("\n")
    print("=" * 60)
    print("ASK AGENT")
    print("=" * 60)

    print(
        "QUESTION |",
        user_question
    )

    # =====================================================
    # 1. CREATE QUERY EMBEDDING
    # =====================================================

    query_embedding = get_query_embedding(
        user_question
    )


    # =====================================================
    # 2. SEMANTIC CACHE
    # =====================================================

    cached_result = find_cached_answer(
        query_embedding
    )


    # =====================================================
    # 3. CACHE HIT
    # =====================================================

    if cached_result:

        cached_sources = cached_result.get(
            "sources",
            []
        )

        print(
            "CACHE RETURN SOURCES |",
            cached_sources
        )

        return {
            "answer": cached_result.get(
                "answer",
                ""
            ),
            "sources": cached_sources
        }


    # =====================================================
    # 4. CACHE MISS → LANGGRAPH
    # =====================================================

    print(
        "CACHE | MISS → running LangGraph"
    )

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }


    # =====================================================
    # 5. INITIAL GRAPH STATE
    # =====================================================

    initial_state = {

        "user_question": user_question,

        "conversation_history": "",

        "topic": "",

        "context": "",

        "confidence": "low",

        "route": "",

        "sources": [],

        "answer": "",

        "error": ""
    }


    # =====================================================
    # 6. RUN GRAPH
    # =====================================================

    result = graph.invoke(
        initial_state,
        config=config
    )


    # =====================================================
    # 7. EXTRACT RESULT
    # =====================================================

    answer = result.get(
        "answer",
        ""
    )

    sources = result.get(
        "sources",
        []
    )


    print(
        "GRAPH RESULT SOURCES |",
        sources
    )


    # =====================================================
    # 8. SAVE TO CACHE
    # =====================================================

    save_cache(
        user_question,
        query_embedding,
        answer,
        sources
    )


    # =====================================================
    # 9. FINAL RESPONSE
    # =====================================================

    print(
        "FINAL AGENT SOURCES |",
        sources
    )

    return {
        "answer": answer,
        "sources": sources
    }
