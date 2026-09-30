from langchain_openai import ChatOpenAI
import os

from dotenv import load_dotenv

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
)


def compress_context(query: str, context: str):

    if not context:
        return ""

    prompt = f"""
You are a context compression system.

User question:
{query}

Retrieved knowledge-base context:
{context}

Task:
Keep ONLY the information that is directly useful
for answering the user's question.

Rules:
- Do not add new information.
- Do not change facts.
- Do not invent anything.
- Remove irrelevant information.
- Preserve important numbers, conditions and limitations.
- Return only the compressed context.
"""

    try:

        response = llm.invoke(prompt)

        return response.content.strip()

    except Exception as e:

        print(f"CONTEXT COMPRESSION ERROR | {e}")

        # Safe fallback:
        # if compression fails, use original context
        return context