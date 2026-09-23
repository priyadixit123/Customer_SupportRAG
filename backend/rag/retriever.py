import os

from dotenv import load_dotenv

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from .bm25_retriever import BM25Retriever
from .hybrid_retriever import HybridRetriever



load_dotenv()


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")

DOCUMENT_PATH = "./documents/knowledge_base.txt"


# =========================================================
# Embeddings
# =========================================================

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)


# =========================================================
# Chroma Vector Store
# =========================================================

vectorstore = Chroma(
    collection_name="holidaybreakz",
    persist_directory=CHROMA_PATH,
    embedding_function=embeddings,
)


# =========================================================
# Vector Retriever
# =========================================================

retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={
        "k": 4
    }
)


# =========================================================
# Load Documents for BM25
# =========================================================

loader = TextLoader(
    DOCUMENT_PATH,
    encoding="utf-8"
)

documents = loader.load()


# =========================================================
# Split Documents
# =========================================================

splitter = RecursiveCharacterTextSplitter(
    chunk_size=700,
    chunk_overlap=100
)

chunks = splitter.split_documents(documents)


# =========================================================
# Add Same Chunk IDs
# =========================================================

for index, chunk in enumerate(chunks):

    chunk.metadata["chunk_id"] = f"kb_{index:03d}"


print(f"Loaded {len(chunks)} chunks for BM25.")


# =========================================================
# BM25 Retriever
# =========================================================

bm25 = BM25Retriever(chunks)
print("Loaded chunks for BM25.")

# =========================================================
# Hybrid Retriever
# =========================================================

hybrid_retriever = HybridRetriever(
    vector_retriever=retriever,
    bm25_retriever=bm25
)

# =========================================================
# Existing Vector Retrieval
# =========================================================

def retrieve_context(query: str):

    documents = retriever.invoke(query)

    if not documents:
        return ""

    context_parts = []

    for document in documents:

        context_parts.append(
            document.page_content
        )

    return "\n\n---\n\n".join(context_parts)


if __name__ == "__main__":

    query = "What is the refund policy?"

    results = hybrid_retriever.search(
        query,
        k=4
    )

    print("\nHYBRID RESULTS\n")

    for rank, result in enumerate(results, start=1):

        document = result["document"]

        print(f"\nRank: {rank}")
        print(
            f"Chunk ID: "
            f"{document.metadata.get('chunk_id')}"
        )
        print(
            f"RRF Score: {result['score']}"
        )
        print(
            document.page_content[:300]
        )