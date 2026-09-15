import os

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma


load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")


embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)


vectorstore = Chroma(
    collection_name="holidaybreakz",
    persist_directory=CHROMA_PATH,
    embedding_function=embeddings,
)


retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={
        "k": 4
    }
)


def retrieve_context(query: str):

    documents = retriever.invoke(query)

    if not documents:
        return ""

    context_parts = []

    for document in documents:
        context_parts.append(document.page_content)

    return "\n\n---\n\n".join(context_parts)