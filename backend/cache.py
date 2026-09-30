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


# --------------------------------------------------
# CREATE CACHE TABLE
# --------------------------------------------------

connection.execute("""
CREATE TABLE IF NOT EXISTS semantic_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    embedding TEXT NOT NULL,
    answer TEXT NOT NULL,
    sources TEXT,
    created_at REAL NOT NULL
)
""")

connection.commit()


# --------------------------------------------------
# ADD SOURCES COLUMN TO EXISTING DATABASE
# --------------------------------------------------

columns = connection.execute(
    "PRAGMA table_info(semantic_cache)"
).fetchall()

column_names = [
    column[1]
    for column in columns
]

if "sources" not in column_names:

    connection.execute(
        """
        ALTER TABLE semantic_cache
        ADD COLUMN sources TEXT
        """
    )

    connection.commit()

    print(
        "CACHE DATABASE | sources column added"
    )


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

def cosine_similarity(
    vector_a,
    vector_b
):

    dot_product = sum(
        a * b
        for a, b in zip(
            vector_a,
            vector_b
        )
    )

    magnitude_a = math.sqrt(
        sum(
            a * a
            for a in vector_a
        )
    )

    magnitude_b = math.sqrt(
        sum(
            b * b
            for b in vector_b
        )
    )

    if (
        magnitude_a == 0
        or magnitude_b == 0
    ):
        return 0

    return dot_product / (
        magnitude_a * magnitude_b
    )


# --------------------------------------------------
# FIND CACHED ANSWER
# --------------------------------------------------

def find_cached_answer(
    query_embedding
):

    rows = connection.execute(
        """
        SELECT
            question,
            embedding,
            answer,
            sources
        FROM semantic_cache
        """
    ).fetchall()


    best_answer = None
    best_sources = []
    best_score = 0


    for (
        question,
        embedding_json,
        answer,
        sources_json
    ) in rows:

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

            if sources_json:

                best_sources = json.loads(
                    sources_json
                )

            else:

                best_sources = []


    # --------------------------------------------------
    # CACHE HIT
    # --------------------------------------------------

    if best_score >= 0.90:

        print(
            f"CACHE HIT | "
            f"similarity={best_score:.3f}"
        )

        return {
            "answer": best_answer,
            "sources": best_sources
        }


    # --------------------------------------------------
    # CACHE MISS
    # --------------------------------------------------

    print(
        f"CACHE MISS | "
        f"similarity={best_score:.3f}"
    )

    return None


# --------------------------------------------------
# SAVE ANSWER + SOURCES TO CACHE
# --------------------------------------------------

def save_cache(
    question: str,
    embedding,
    answer: str,
    sources=None
):

    fallback_message = (
        "Please contact HolidayBreakz support "
        "for the most accurate information."
    )


    # --------------------------------------------------
    # Do not cache fallback responses
    # --------------------------------------------------

    if (
        not answer
        or fallback_message in answer
    ):

        print(
            "CACHE SKIP | fallback answer"
        )

        return


    if sources is None:
        sources = []


    # --------------------------------------------------
    # Save
    # --------------------------------------------------

    connection.execute(
        """
        INSERT INTO semantic_cache
        (
            question,
            embedding,
            answer,
            sources,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            question,
            json.dumps(embedding),
            answer,
            json.dumps(sources),
            time.time()
        )
    )


    connection.commit()


    print(
        "Answer + sources saved "
        "to semantic cache."
    )
