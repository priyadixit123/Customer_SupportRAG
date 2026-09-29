import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

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


def generate_queries(query: str):

    prompt = f"""
Generate 3 different search queries for the following
customer-support question.

Rules:
- Keep the same meaning.
- Use different wording.
- Focus on important keywords.
- Make each query useful for knowledge-base search.
- Return only 3 queries.
- Return one query per line.

Customer question:
{query}
"""

    response = llm.invoke(prompt)

    generated_queries = [
        line.strip()
        for line in response.content.splitlines()
        if line.strip()
    ]

    queries = [query] + generated_queries[:3]

    # Remove duplicates
    unique_queries = list(dict.fromkeys(queries))

    return unique_queries