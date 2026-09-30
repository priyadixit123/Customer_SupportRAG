import os
import re
import shutil

from dotenv import load_dotenv

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma


load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")

if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY is missing in .env")


DOCUMENT_PATH = "./documents/knowledge_base.txt"


def detect_section(text):

    text_lower = text.lower()

    if "seat" in text_lower:
        return "Seats"

    if "baggage" in text_lower or "bag" in text_lower:
        return "Baggage"

    if "meal" in text_lower:
        return "Meals"

    if "refund" in text_lower:
        return "Refunds"

    if "booking" in text_lower:
        return "Booking"

    if "cancellation" in text_lower:
        return "Cancellation"

    return "General"


def detect_topic(text):

    text_lower = text.lower()

    if "seat" in text_lower:
        return "seat_selection"

    if "baggage" in text_lower or "bag" in text_lower:
        return "baggage"

    if "meal" in text_lower:
        return "meals"

    if "refund shield" in text_lower:
        return "refund_shield"

    if "cancellation protection" in text_lower:
        return "cancellation_protection"

    if "refund" in text_lower:
        return "refund"

    if "booking" in text_lower:
        return "booking"

    return "general"


def ingest():

    print("Loading knowledge base...")

    loader = TextLoader(
        DOCUMENT_PATH,
        encoding="utf-8"
    )

    documents = loader.load()

    print(f"Loaded {len(documents)} document(s)")

    # --------------------------------
    # Better chunking
    # --------------------------------

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=100,
        separators=[
            "\n\n",
            "\n",
            ". ",
            "? ",
            "! ",
            " ",
            ""
        ]
    )

    chunks = splitter.split_documents(documents)

    print(f"Created {len(chunks)} chunks")

    # --------------------------------
    # Add metadata
    # --------------------------------

    for index, chunk in enumerate(chunks):

        chunk.metadata["chunk_id"] = f"kb_{index:03d}"

        chunk.metadata["source"] = "knowledge_base.txt"

        chunk.metadata["section"] = detect_section(
            chunk.page_content
        )

        chunk.metadata["topic"] = detect_topic(
            chunk.page_content
        )

    print("Chunk metadata created.")
    print(chunks[0].metadata)

    # --------------------------------
    # Show metadata
    # --------------------------------

    for chunk in chunks[:5]:

        print(
            "\n",
            chunk.metadata["chunk_id"],
            "|",
            chunk.metadata["section"],
            "|",
            chunk.metadata["topic"]
        )

        print(
            chunk.page_content[:120]
        )

    # --------------------------------
    # Create embeddings
    # --------------------------------

    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
    )

    # --------------------------------
    # Remove old Chroma database
    # --------------------------------

    if os.path.exists(CHROMA_PATH):

        print("\nRemoving old Chroma database...")

        shutil.rmtree(CHROMA_PATH)

    # --------------------------------
    # Create Chroma database
    # --------------------------------

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PATH,
        collection_name="holidaybreakz"
    )

    print("\nRAG database created successfully.")
    print(f"Location: {CHROMA_PATH}")


if __name__ == "__main__":
    ingest()