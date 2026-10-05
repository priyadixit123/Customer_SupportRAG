import os

from dotenv import load_dotenv

from .reranker import Reranker

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

from .bm25_retriever import BM25Retriever
from .hybrid_retriever import HybridRetriever
from .multi_query import generate_queries
from .context_compressor import compress_context


load_dotenv()


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DOCUMENT_PATH = os.path.join(
    BASE_DIR,
    "documents",
    "knowledge_base.txt"
)


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

chunks = splitter.split_documents(
    documents
)


# =========================================================
# Metadata Detection
# =========================================================

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


for index, chunk in enumerate(chunks):

    chunk.metadata["chunk_id"] = (
        f"kb_{index:03d}"
    )

    chunk.metadata["source"] = (
        "knowledge_base.txt"
    )

    chunk.metadata["section"] = (
        detect_section(
            chunk.page_content
        )
    )

    chunk.metadata["topic"] = (
        detect_topic(
            chunk.page_content
        )
    )


# =========================================================
# BM25 Retriever
# =========================================================

bm25 = BM25Retriever(
    chunks
)

print(
    "Loaded chunks for BM25."
)


# =========================================================
# Hybrid Retriever
# =========================================================

hybrid_retriever = HybridRetriever(
    vector_retriever=retriever,
    bm25_retriever=bm25
)


# =========================================================
# CrossEncoder Reranker
# =========================================================

reranker = Reranker()


# =========================================================
# Retrieve Context
# =========================================================

def retrieve_context(
    query: str,
    k: int = 4
):

    # -----------------------------------------------------
    # Multi-query retrieval
    # -----------------------------------------------------

    queries = generate_queries(
        query
    )

    all_results = []

    for search_query in queries:

        results = hybrid_retriever.search(
            search_query,
            k=8
        )

        all_results.extend(
            results
        )


    # -----------------------------------------------------
    # No results
    # -----------------------------------------------------

    if not all_results:

        return {
            "context": "",
            "score": None,
            "sources": []
        }


    # -----------------------------------------------------
    # Remove duplicate documents
    # -----------------------------------------------------

    unique_documents = {}

    for result in all_results:

        document = result["document"]

        doc_id = document.metadata.get(
            "chunk_id",
            document.page_content
        )

        unique_documents[
            doc_id
        ] = document


    documents = list(
        unique_documents.values()
    )


    # -----------------------------------------------------
    # CrossEncoder reranking
    # -----------------------------------------------------

    reranked_results = reranker.rerank(
        query,
        documents,
        k=k
    )


    # -----------------------------------------------------
    # No reranked results
    # -----------------------------------------------------

    if not reranked_results:

        return {
            "context": "",
            "score": None,
            "sources": []
        }


    # -----------------------------------------------------
    # Build context + source tracking
    # -----------------------------------------------------

    context_parts = []

    sources = []


    for result in reranked_results:

        document = result["document"]


        # Context
        context_parts.append(
            document.page_content
        )






        # Source information
        source = {

            "chunk_id": document.metadata.get(
                "chunk_id",
                "unknown"
            ),

            "section": document.metadata.get(
                "section",
                "unknown"
            ),

            "topic": document.metadata.get(
                "topic",
                "unknown"
            ),

            "source": document.metadata.get(
                "source",



            )
        }

        sources.append(
            source
        )


    # -----------------------------------------------------
    # Combine retrieved context
    # -----------------------------------------------------

    raw_context = (
        "\n\n---\n\n".join(
            context_parts
        )
    )


    # -----------------------------------------------------
    # Context Compression
    # -----------------------------------------------------

    compressed_context = compress_context(
        query,
        raw_context
    )


    # -----------------------------------------------------
    # Best CrossEncoder score
    # -----------------------------------------------------

    best_score = (
        reranked_results[0]["score"]
    )


    print(
        f"BEST RERANKER SCORE | "
        f"{best_score:.3f}"
    )

    print(
        "CONTEXT COMPRESSION | completed"
    )

    print( "RETRIEVER SOURCES |", sources )


    # -----------------------------------------------------
    # Final retrieval result
    # -----------------------------------------------------

    return {

        "context": compressed_context,

        "score": best_score,

        "sources": sources

    }


# =========================================================
# Retrieval Documents
# Used by Evaluation
# =========================================================

def retrieve_documents(
    query: str,
    k: int = 4
):

    """
    Returns retrieved Document objects
    with RRF scores.

    Used for evaluation.
    """

    return hybrid_retriever.search(
        query,
        k=k
    )


# =========================================================
# Query Topic Detection
# =========================================================

def detect_query_topic(
    query: str
):

    query_lower = query.lower()


    if "seat" in query_lower:
        return "seat_selection"


    if (
        "baggage" in query_lower
        or "bag" in query_lower
    ):
        return "baggage"


    if "meal" in query_lower:
        return "meals"


    if "refund shield" in query_lower:
        return "refund_shield"


    if "cancellation protection" in query_lower:
        return "cancellation_protection"


    if "refund" in query_lower:
        return "refund"


    if "booking" in query_lower:
        return "booking"


    return None


# =========================================================
# Vector Search With Metadata Filtering
# =========================================================

def vector_search(
    query: str,
    k: int = 4
):

    topic = detect_query_topic(
        query
    )


    if topic:

        print(
            f"METADATA FILTER | "
            f"topic={topic}"
        )

        return vectorstore.similarity_search(
            query,
            k=k,
            filter={
                "topic": topic
            }
        )


    print(
        "METADATA FILTER | none"
    )


    return vectorstore.similarity_search(
        query,
        k=k
    )

