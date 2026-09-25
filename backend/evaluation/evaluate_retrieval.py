import json
from pathlib import Path

from rag.retriever import hybrid_retriever, retriever
from rag.bm25_retriever import BM25Retriever
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


K = 4


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


for index, chunk in enumerate(chunks):
    chunk.metadata["chunk_id"] = f"kb_{index:03d}"


bm25 = BM25Retriever(chunks)


# =========================================================
# Load Evaluation Dataset
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "eval_dataset.json"

with open(DATASET_PATH, "r", encoding="utf-8") as f:
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

    results = bm25.search(question, k=K)

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
# MRR
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

    total_recall = 0
    total_precision = 0
    total_hit_rate = 0
    total_mrr = 0

    print()
    print("=" * 60)
    print(name)
    print("=" * 60)

    for item in dataset:

        question = item["question"]

        relevant = item["relevant_chunk_ids"]

        retrieved = search_function(question)

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

        total_recall += recall
        total_precision += precision
        total_hit_rate += hit_rate
        total_mrr += mrr

        print()
        print("Question:", question)
        print("Relevant:", relevant)
        print("Retrieved:", retrieved)
        print(
            f"Recall@{K}: {recall:.2f}"
        )
        print(
            f"Precision@{K}: {precision:.2f}"
        )
        print(
            f"Hit Rate@{K}: {hit_rate:.2f}"
        )
        print(
            f"MRR: {mrr:.2f}"
        )

    count = len(dataset)

    print()
    print("AVERAGE")
    print("-" * 40)

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

    evaluate(
        "VECTOR SEARCH",
        vector_search
    )

    evaluate(
        "BM25 SEARCH",
        bm25_search
    )

    evaluate(
        "HYBRID RRF",
        hybrid_search
    )