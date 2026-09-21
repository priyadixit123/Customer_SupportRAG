import os
import sqlite3
import json
import time
import math

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings


# --------------------------------------------------
# ENVIRONMENT
# --------------------------------------------------

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    raise ValueError(
        "OPENROUTER_API_KEY is missing in .env"
    )


# --------------------------------------------------
# EMBEDDING MODEL
# --------------------------------------------------

embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)


# --------------------------------------------------
# SQLITE CACHE
# --------------------------------------------------

CACHE_DB = "holidaybreakz_cache.db"

connection = sqlite3.connect(
    CACHE_DB,
    check_same_thread=False
)


connection.execute("""
CREATE TABLE IF NOT EXISTS semantic_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    embedding TEXT NOT NULL,
    answer TEXT NOT NULL,
    created_at REAL NOT NULL
)
""")

connection.commit()


# --------------------------------------------------
# CREATE QUERY EMBEDDING
# --------------------------------------------------

def get_query_embedding(question: str):

    embedding = embedding_model.embed_query(
        question
    )

    return embedding


# --------------------------------------------------
# COSINE SIMILARITY
# --------------------------------------------------

def cosine_similarity(vector_a, vector_b):

    dot_product = sum(
        a * b
        for a, b in zip(vector_a, vector_b)
    )

    magnitude_a = math.sqrt(
        sum(a * a for a in vector_a)
    )

    magnitude_b = math.sqrt(
        sum(b * b for b in vector_b)
    )

    if magnitude_a == 0 or magnitude_b == 0:
        return 0

    return dot_product / (
        magnitude_a * magnitude_b
    )


# --------------------------------------------------
# FIND CACHED ANSWER
# --------------------------------------------------

def find_cached_answer(query_embedding):

    rows = connection.execute(
        """
        SELECT question, embedding, answer
        FROM semantic_cache
        """
    ).fetchall()

    best_answer = None
    best_score = 0

    for question, embedding_json, answer in rows:

        cached_embedding = json.loads(
            embedding_json
        )

        score = cosine_similarity(
            query_embedding,
            cached_embedding
        )

        if score > best_score:

            best_score = score
            best_answer = answer

    if best_score >= 0.90:

        print(
            f"CACHE HIT | similarity={best_score:.3f}"
        )

        return best_answer

    print(
        f"CACHE MISS | similarity={best_score:.3f}"
    )

    return None


# --------------------------------------------------
# SAVE ANSWER TO CACHE
# --------------------------------------------------

def save_cache(
    question: str,
    embedding,
    answer: str
):

    connection.execute(
        """
        INSERT INTO semantic_cache
        (question, embedding, answer, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            question,
            json.dumps(embedding),
            answer,
            time.time()
        )
    )

    connection.commit()

    print("Answer saved to semantic cache.")