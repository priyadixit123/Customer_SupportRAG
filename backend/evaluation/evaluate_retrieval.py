import json
from pathlib import Path

from rag.reranker import Reranker

from rag.retriever import hybrid_retriever, retriever
from rag.bm25_retriever import BM25Retriever

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


# =========================================================
# Configuration
# =========================================================

K = 4

# Hybrid will first retrieve more candidates.
# Reranker will then select the final K documents.
RERANK_CANDIDATES = 8


# =========================================================
# Load BM25
# =========================================================

loader = TextLoader(
    "./documents/knowledge_base.txt",
    encoding="utf-8"
)

documents = loader.load()


splitter = RecursiveCharacterTextSplitter(
    chunk_size=700,
    chunk_overlap=100
)

chunks = splitter.split_documents(documents)


# =========================================================
# Assign Stable Chunk IDs
# =========================================================

for index, chunk in enumerate(chunks):

    chunk.metadata["chunk_id"] = f"kb_{index:03d}"


# =========================================================
# Create BM25 Retriever
# =========================================================

bm25 = BM25Retriever(chunks)


# =========================================================
# Create Reranker
# =========================================================

reranker = Reranker()


# =========================================================
# Load Evaluation Dataset
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

DATASET_PATH = BASE_DIR / "eval_dataset.json"


with open(
    DATASET_PATH,
    "r",
    encoding="utf-8"
) as f:

    dataset = json.load(f)


# =========================================================
# Get Chunk ID
# =========================================================

def get_chunk_id(document):

    return document.metadata.get(
        "chunk_id",
        document.page_content
    )


# =========================================================
# Vector Retrieval
# =========================================================

def vector_search(question):

    documents = retriever.invoke(question)

    return [
        get_chunk_id(document)
        for document in documents[:K]
    ]


# =========================================================
# BM25 Retrieval
# =========================================================

def bm25_search(question):

    results = bm25.search(
        question,
        k=K
    )

    return [
        get_chunk_id(result["document"])
        for result in results
    ]


# =========================================================
# Hybrid Retrieval
# =========================================================

def hybrid_search(question):

    results = hybrid_retriever.search(
        question,
        k=K
    )

    return [
        get_chunk_id(result["document"])
        for result in results
    ]


# =========================================================
# Hybrid + Reranker
# =========================================================

def reranked_search(question):

    # -----------------------------------------------------
    # Step 1
    # Get more candidates from Hybrid RRF
    # -----------------------------------------------------

    results = hybrid_retriever.search(
        question,
        k=RERANK_CANDIDATES
    )

    if not results:

        return []


    # -----------------------------------------------------
    # Step 2
    # Extract documents
    # -----------------------------------------------------

    documents = [
        result["document"]
        for result in results
    ]


    # -----------------------------------------------------
    # Step 3
    # Rerank candidates
    # -----------------------------------------------------

    reranked_results = reranker.rerank(
        question,
        documents,
        k=K
    )


    # -----------------------------------------------------
    # Step 4
    # Return final chunk IDs
    # -----------------------------------------------------

    return [
        get_chunk_id(result["document"])
        for result in reranked_results
    ]


# =========================================================
# Recall@K
# =========================================================

def recall_at_k(retrieved, relevant):

    relevant = set(relevant)

    if not relevant:

        return 0.0


    retrieved = set(retrieved)

    return (
        len(retrieved & relevant)
        / len(relevant)
    )


# =========================================================
# Precision@K
# =========================================================

def precision_at_k(retrieved, relevant):

    relevant = set(relevant)

    if not retrieved:

        return 0.0


    retrieved = set(retrieved)

    return (
        len(retrieved & relevant)
        / len(retrieved)
    )


# =========================================================
# Hit Rate@K
# =========================================================

def hit_rate_at_k(retrieved, relevant):

    relevant = set(relevant)

    if not relevant:

        return 0.0


    return 1.0 if any(
        chunk_id in relevant
        for chunk_id in retrieved
    ) else 0.0


# =========================================================
# Mean Reciprocal Rank
# =========================================================

def reciprocal_rank(retrieved, relevant):

    relevant = set(relevant)


    for rank, chunk_id in enumerate(
        retrieved,
        start=1
    ):

        if chunk_id in relevant:

            return 1.0 / rank


    return 0.0


# =========================================================
# Evaluate Retriever
# =========================================================

def evaluate(name, search_function):

    total_recall = 0.0
    total_precision = 0.0
    total_hit_rate = 0.0
    total_mrr = 0.0


    print()
    print("=" * 70)
    print(name)
    print("=" * 70)


    for item in dataset:

        question = item["question"]

        relevant = item["relevant_chunk_ids"]


        # -------------------------------------------------
        # Retrieve
        # -------------------------------------------------

        retrieved = search_function(question)


        # -------------------------------------------------
        # Calculate Metrics
        # -------------------------------------------------

        recall = recall_at_k(
            retrieved,
            relevant
        )


        precision = precision_at_k(
            retrieved,
            relevant
        )


        hit_rate = hit_rate_at_k(
            retrieved,
            relevant
        )


        mrr = reciprocal_rank(
            retrieved,
            relevant
        )


        # -------------------------------------------------
        # Add to totals
        # -------------------------------------------------

        total_recall += recall

        total_precision += precision

        total_hit_rate += hit_rate

        total_mrr += mrr


        # -------------------------------------------------
        # Print Question Result
        # -------------------------------------------------

        print()

        print("Question:")
        print(question)


        print()

        print("Relevant:")
        print(relevant)


        print()

        print("Retrieved:")
        print(retrieved)


        print()

        print(
            f"Recall@{K}: "
            f"{recall:.2f}"
        )


        print(
            f"Precision@{K}: "
            f"{precision:.2f}"
        )


        print(
            f"Hit Rate@{K}: "
            f"{hit_rate:.2f}"
        )


        print(
            f"MRR: "
            f"{mrr:.2f}"
        )


    # =====================================================
    # Average Metrics
    # =====================================================

    count = len(dataset)


    print()
    print("=" * 70)
    print(f"AVERAGE - {name}")
    print("=" * 70)


    print(
        f"Recall@{K}: "
        f"{total_recall / count:.3f}"
    )


    print(
        f"Precision@{K}: "
        f"{total_precision / count:.3f}"
    )


    print(
        f"Hit Rate@{K}: "
        f"{total_hit_rate / count:.3f}"
    )


    print(
        f"MRR: "
        f"{total_mrr / count:.3f}"
    )


# =========================================================
# Run Evaluation
# =========================================================

if __name__ == "__main__":

    # -----------------------------------------------------
    # 1. Vector Search
    # -----------------------------------------------------

    evaluate(
        "VECTOR SEARCH",
        vector_search
    )


    # -----------------------------------------------------
    # 2. BM25 Search
    # -----------------------------------------------------

    evaluate(
        "BM25 SEARCH",
        bm25_search
    )


    # -----------------------------------------------------
    # 3. Hybrid RRF
    # -----------------------------------------------------

    evaluate(
        "HYBRID RRF",
        hybrid_search
    )


    # -----------------------------------------------------
    # 4. Hybrid + Reranker
    # -----------------------------------------------------

    evaluate(
        "HYBRID + RERANKER",
        reranked_search
    )