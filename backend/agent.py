import os
import sqlite3
from typing import TypedDict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from langgraph.graph import StateGraph, START, END
from langgraph.types import RetryPolicy
from langgraph.checkpoint.sqlite import SqliteSaver

from rag.retriever import retrieve_context

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
    answer: str
    error: str


# --------------------------------------------------
# RETRIEVE NODE
# --------------------------------------------------

def retrieve_node(state: AgentState):

    try:
        question = state["user_question"]

        context = retrieve_context(question)

        return {
            "context": context,
            "error": ""
        }

    except Exception as e:

        return {
            "context": "",
            "error": str(e)
        }


# --------------------------------------------------
# LLM NODE
# --------------------------------------------------

def llm_node(state: AgentState):

    context = state["context"]
    question = state["user_question"]

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
"""

    response = llm.invoke(prompt)

    return {
        "answer": response.content,
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


# --------------------------------------------------
# GRAPH FLOW
# --------------------------------------------------

builder.add_edge(
    START,
    "retrieve"
)

builder.add_edge(
    "retrieve",
    "llm"
)

builder.add_edge(
    "llm",
    END
)


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
            "context": "",
            "answer": "",
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