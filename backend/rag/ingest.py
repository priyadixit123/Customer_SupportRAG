import os
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


def ingest():

    print("Loading knowledge base...")

    loader = TextLoader(
        DOCUMENT_PATH,
        encoding="utf-8"
    )

    documents = loader.load()

    print(f"Loaded {len(documents)} document(s)")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=100
    )

    chunks = splitter.split_documents(documents)

    print(f"Created {len(chunks)} chunks")

    # --------------------------------
    # Add stable chunk IDs
    # --------------------------------

    for index, chunk in enumerate(chunks):

        chunk.metadata["chunk_id"] = f"kb_{index:03d}"

    print("Chunk IDs created.")

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

        print("Removing old Chroma database...")

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

    print("RAG database created successfully.")
    print(f"Location: {CHROMA_PATH}")

    # --------------------------------
    # Show chunk IDs
    # --------------------------------

    for chunk in chunks[:5]:

        print(
            chunk.metadata["chunk_id"],
            "=>",
            chunk.page_content[:80]
        )


if __name__ == "__main__":
    ingest()