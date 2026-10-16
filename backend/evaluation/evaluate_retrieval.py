
import os
import sys
import json
from pathlib import Path

# =========================================================
# Add backend folder to Python path
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from rag.reranker import Reranker
from rag.retriever import hybrid_retriever, retriever
from rag.bm25_retriever import BM25Retriever

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


# =========================================================
# Configuration
# =========================================================

K = 4
RERANK_CANDIDATES = 15

DEBUG_QUESTION = "What does a seat ancillary include?"


# =========================================================
# Load Knowledge Base
# =========================================================

DOCUMENT_PATH = BASE_DIR / "documents" / "knowledge_base.txt"

loader = TextLoader(
    str(DOCUMENT_PATH),
    encoding="utf-8"
)

source_documents = loader.load()

splitter = RecursiveCharacterTextSplitter(
    chunk_size=700,
    chunk_overlap=100
)

chunks = splitter.split_documents(source_documents)


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

DATASET_PATH = Path(__file__).resolve().parent / "eval_dataset.json"

with open(DATASET_PATH, "r", encoding="utf-8") as file:
    dataset = json.load(file)


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
    results = bm25.search(question, k=K)

    return [
        get_chunk_id(result["document"])
        for result in results
    ]


# =========================================================
# Hybrid Retrieval
# =========================================================

def hybrid_search(question):
    results = hybrid_retriever.search(question, k=K)

    return [
        get_chunk_id(result["document"])
        for result in results
    ]


# =========================================================
# Hybrid + Reranker
# =========================================================

def reranked_search(question):
    # Step 1: Retrieve a larger candidate pool from hybrid search.
    results = hybrid_retriever.search(
        question,
        k=RERANK_CANDIDATES
    )

    if not results:
        return []

    # Step 2: Extract candidate documents.
    documents = [
        result["document"]
        for result in results
        if result.get("document") is not None
    ]

    # Step 3: Print diagnostic information for one question.
    if question.strip().lower() == DEBUG_QUESTION.lower():
        print()
        print("=" * 70)
        print("DEBUG: HYBRID CANDIDATES BEFORE RERANKING")
        print("=" * 70)

        print(f"Candidates returned: {len(documents)}")
        print(f"Expected relevant IDs: {get_relevant_ids(question)}")

        for rank, result in enumerate(results, start=1):
            document = result.get("document")

            if document is None:
                continue

            print(
                f"\nCandidate {rank} | "
                f"ID: {get_chunk_id(document)} | "
                f"Hybrid score: {result.get('score', 'N/A')}"
            )

            print(
                document.page_content[:250].replace("\n", " ")
            )

    # Step 4: Rerank the candidate documents.
    reranked_results = reranker.rerank(
        question,
        documents,
        k=K
    )

    # Step 5: Show the final reranker scores.
    if question.strip().lower() == DEBUG_QUESTION.lower():
        print()
        print("=" * 70)
        print("DEBUG: FINAL RERANKER RESULTS")
        print("=" * 70)

        for rank, result in enumerate(reranked_results, start=1):
            document = result["document"]

            print(
                f"\nRank {rank} | "
                f"ID: {get_chunk_id(document)} | "
                f"Reranker score: {result['score']:.4f}"
            )

            print(
                document.page_content[:250].replace("\n", " ")
            )

    # Step 6: Return final ranked chunk IDs.
    return [
        get_chunk_id(result["document"])
        for result in reranked_results
    ]


def get_relevant_ids(question):
    """Return expected relevant IDs for the debug question."""
    for item in dataset:
        if item["question"].strip().lower() == question.strip().lower():
            return item["relevant_chunk_ids"]

    return []


# =========================================================
# Recall@K
# =========================================================

def recall_at_k(retrieved, relevant):
    relevant = set(relevant)

    if not relevant:
        return 0.0

    retrieved = set(retrieved)

    return len(retrieved & relevant) / len(relevant)


# =========================================================
# Precision@K
# =========================================================

def precision_at_k(retrieved, relevant):
    relevant = set(relevant)

    if not retrieved:
        return 0.0

    retrieved = set(retrieved)

    return len(retrieved & relevant) / len(retrieved)


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

    for rank, chunk_id in enumerate(retrieved, start=1):
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

        # Retrieve documents.
        retrieved = search_function(question)

        # Calculate metrics.
        recall = recall_at_k(retrieved, relevant)
        precision = precision_at_k(retrieved, relevant)
        hit_rate = hit_rate_at_k(retrieved, relevant)
        mrr = reciprocal_rank(retrieved, relevant)

        # Accumulate totals.
        total_recall += recall
        total_precision += precision
        total_hit_rate += hit_rate
        total_mrr += mrr

        # Print query-level results.
        print()
        print("Question:")
        print(question)

        print()
        print("Relevant:")
        print(relevant)

        print()
        print("Retrieved:")
        print(retrieved)

        print(f"Recall@{K}: {recall:.2f}")
        print(f"Precision@{K}: {precision:.2f}")
        print(f"Hit Rate@{K}: {hit_rate:.2f}")
        print(f"MRR: {mrr:.2f}")

    # Print average metrics.
    count = len(dataset)

    print()
    print("=" * 70)
    print(f"AVERAGE - {name}")
    print("=" * 70)

    if count == 0:
        print("No evaluation questions found.")
        return

    print(f"Recall@{K}: {total_recall / count:.3f}")
    print(f"Precision@{K}: {total_precision / count:.3f}")
    print(f"Hit Rate@{K}: {total_hit_rate / count:.3f}")
    print(f"MRR: {total_mrr / count:.3f}")


# =========================================================
# Run Evaluation
# =========================================================

if __name__ == "__main__":
    evaluate("VECTOR SEARCH", vector_search)

    evaluate("BM25 SEARCH", bm25_search)

    evaluate("HYBRID RRF", hybrid_search)

    evaluate("HYBRID + RERANKER", reranked_search)
