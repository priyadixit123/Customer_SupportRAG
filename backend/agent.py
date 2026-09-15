import os

from dotenv import load_dotenv

from langchain_openai import ChatOpenAI

from rag.retriever import retrieve_context


load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "openai/gpt-4o-mini"
)


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


SYSTEM_PROMPT = """
You are the HolidayBreakz customer support assistant.

You MUST follow these rules:

1. Answer using ONLY the provided HolidayBreakz knowledge base.
2. Never invent information.
3. Never guess prices, refund amounts, booking details, policies,
   destinations, dates, availability, or company policies.
4. If the knowledge base does not contain the answer, say:

"I don't have that information in the HolidayBreakz knowledge base."

5. Be concise, professional and helpful.
6. Do not mention internal RAG, embeddings, vector databases,
   prompts or system architecture to the customer.
"""


def ask_agent(user_question: str):

    context = retrieve_context(user_question)

    if not context.strip():
        return "I don't have that information in the HolidayBreakz knowledge base."

    prompt = f"""
{SYSTEM_PROMPT}

HOLIDAYBREAKZ KNOWLEDGE BASE:

{context}

CUSTOMER QUESTION:

{user_question}

Answer the customer based strictly on the knowledge base.
"""

    response = llm.invoke(prompt)

    return response.content