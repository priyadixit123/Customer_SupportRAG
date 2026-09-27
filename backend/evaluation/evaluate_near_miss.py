import sys
import json
from pathlib import Path


# =========================================================
# ADD BACKEND DIRECTORY TO PYTHON PATH
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


# =========================================================
# IMPORTS
# =========================================================

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag.retriever import (
    retriever,
    bm25,
    hybrid_retriever,
    reranker
)


# =========================================================
# PATHS
# =========================================================

DOCUMENT_PATH = (
    BASE_DIR
    / "documents"
    / "knowledge_base.txt"
)

DATASET_PATH = (
    Path(__file__).resolve().parent
    / "near_miss_dataset.json"
)


# =========================================================
# LOAD KNOWLEDGE BASE
# =========================================================

loader = TextLoader(
    str(DOCUMENT_PATH),
    encoding="utf-8"
)

documents = loader.load()


splitter = RecursiveCharacterTextSplitter(
    chunk_size=700,
    chunk_overlap=100
)

chunks = splitter.split_documents(
    documents
)


# =========================================================
# ADD CHUNK IDS
# =========================================================

for index, chunk in enumerate(chunks):

    chunk.metadata["chunk_id"] = (
        f"kb_{index:03d}"
    )


# =========================================================
# LOAD DATASET
# =========================================================

with open(
    DATASET_PATH,
    "r",
    encoding="utf-8"
) as file:

    dataset = json.load(file)


# =========================================================
# SEARCH FUNCTIONS
# =========================================================

def vector_search(question, k=4):

    return retriever.invoke(
        question
    )


def bm25_search(question, k=4):

    results = bm25.search(
        question,
        k=k
    )

    return [
        item["document"]
        for item in results
    ]


def hybrid_search(question, k=4):

    results = hybrid_retriever.search(
        question,
        k=k
    )

    return [
        item["document"]
        for item in results
    ]


def reranked_search(question, k=4):

    # Get more candidates first
    hybrid_results = hybrid_retriever.search(
        question,
        k=8
    )

    documents = [
        item["document"]
        for item in hybrid_results
    ]

    results = reranker.rerank(
        question,
        documents,
        k=k
    )

    return [
        item["document"]
        for item in results
    ]


# =========================================================
# CHUNK IDS
# =========================================================

def get_chunk_ids(documents):

    return [
        document.metadata.get(
            "chunk_id"
        )
        for document in documents
    ]


# =========================================================
# HIT CHECK
# =========================================================

def is_hit(
    retrieved_ids,
    relevant_ids
):

    return any(
        chunk_id in relevant_ids
        for chunk_id in retrieved_ids
    )


# =========================================================
# EVALUATE QUESTION
# =========================================================

def evaluate_question(
    question,
    relevant_ids
):

    vector_docs = vector_search(
        question
    )

    bm25_docs = bm25_search(
        question
    )

    hybrid_docs = hybrid_search(
        question
    )

    reranked_docs = reranked_search(
        question
    )

    vector_ids = get_chunk_ids(
        vector_docs
    )

    bm25_ids = get_chunk_ids(
        bm25_docs
    )

    hybrid_ids = get_chunk_ids(
        hybrid_docs
    )

    reranked_ids = get_chunk_ids(
        reranked_docs
    )

    return {

        "vector": is_hit(
            vector_ids,
            relevant_ids
        ),

        "bm25": is_hit(
            bm25_ids,
            relevant_ids
        ),

        "hybrid": is_hit(
            hybrid_ids,
            relevant_ids
        ),

        "reranked": is_hit(
            reranked_ids,
            relevant_ids
        ),

        "vector_ids": vector_ids,

        "bm25_ids": bm25_ids,

        "hybrid_ids": hybrid_ids,

        "reranked_ids": reranked_ids
    }


# =========================================================
# MAIN
# =========================================================

def main():

    methods = [
        "vector",
        "bm25",
        "hybrid",
        "reranked"
    ]

    totals = {

        method: {
            "specific": 0,
            "generic": 0
        }

        for method in methods
    }

    total_specific = 0
    total_generic = 0


    print()
    print("=" * 90)
    print("NEAR-MISS RETRIEVAL EVALUATION")
    print("=" * 90)


    # =====================================================
    # LOOP THROUGH PAIRS
    # =====================================================

    for pair in dataset:

        print()
        print("-" * 90)

        print(
            "PAIR:",
            pair["pair_id"]
        )


        # =================================================
        # SPECIFIC QUESTION
        # =================================================

        specific_question = (
            pair["specific_question"]
        )

        specific_expected = (
            pair["specific_relevant_chunk_ids"]
        )

        specific_result = evaluate_question(
            specific_question,
            specific_expected
        )


        print()
        print("SPECIFIC:")
        print(
            specific_question
        )

        print(
            "Expected:",
            specific_expected
        )


        for method in methods:

            print(
                f"{method.upper():10}:",
                specific_result[method],
                specific_result[
                    f"{method}_ids"
                ]
            )

            if specific_result[method]:

                totals[method][
                    "specific"
                ] += 1


        total_specific += 1


        # =================================================
        # GENERIC QUESTION
        # =================================================

        generic_question = (
            pair["generic_question"]
        )

        generic_expected = (
            pair["generic_relevant_chunk_ids"]
        )

        generic_result = evaluate_question(
            generic_question,
            generic_expected
        )


        print()
        print("GENERIC:")
        print(
            generic_question
        )

        print(
            "Expected:",
            generic_expected
        )


        for method in methods:

            print(
                f"{method.upper():10}:",
                generic_result[method],
                generic_result[
                    f"{method}_ids"
                ]
            )

            if generic_result[method]:

                totals[method][
                    "generic"
                ] += 1


        total_generic += 1


    # =====================================================
    # SUMMARY
    # =====================================================

    print()
    print("=" * 90)
    print("NEAR-MISS SUMMARY")
    print("=" * 90)

    print(
        f"Specific questions: {total_specific}"
    )

    print(
        f"Generic questions:  {total_generic}"
    )

    print()


    for method in methods:

        specific_hits = (
            totals[method]["specific"]
        )

        generic_hits = (
            totals[method]["generic"]
        )

        specific_rate = (
            specific_hits / total_specific
            if total_specific
            else 0
        )

        generic_rate = (
            generic_hits / total_generic
            if total_generic
            else 0
        )

        print(
            f"{method.upper():10} | "
            f"Specific: "
            f"{specific_hits}/{total_specific} "
            f"({specific_rate:.2%}) | "
            f"Generic: "
            f"{generic_hits}/{total_generic} "
            f"({generic_rate:.2%})"
        )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    main()