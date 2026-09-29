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
    bm25_retriever=bm25,
    
)
reranker = Reranker()

# =========================================================
# Existing Vector Retrieval
# =========================================================

def retrieve_context(query: str, k: int = 4):

    queries = generate_queries(query)

    all_results = []

    for search_query in queries:

        results = hybrid_retriever.search(
            search_query,
            k=8
        )

        all_results.extend(results)

    if not all_results:
        return {
            "context": "",
            "score": None
        }

    # Remove duplicate documents
    unique_documents = {}

    for result in all_results:

        document = result["document"]

        doc_id = document.metadata.get(
            "chunk_id",
            document.page_content
        )

        unique_documents[doc_id] = document

    documents = list(
        unique_documents.values()
    )

    # CrossEncoder reranking
    reranked_results = reranker.rerank(
        query,
        documents,
        k=k
    )

    if not reranked_results:
        return {
            "context": "",
            "score": None
        }

    context_parts = []

    for result in reranked_results:

        document = result["document"]

        context_parts.append(
            document.page_content
        )

    best_score = reranked_results[0]["score"]

    print(
        f"BEST RERANKER SCORE | {best_score:.3f}"
    )

    return {
        "context": "\n\n---\n\n".join(context_parts),
        "score": best_score
    }


def retrieve_documents(query: str, k: int = 4):
    """
    Returns retrieved Document objects with RRF scores.
    Used for evaluation.
    """
    return hybrid_retriever.search(query, k=k)
