
# HolidayBreakz Customer Support AI – Complete Journey

## Final Architecture

![Optimise LLM usage costs with Semantic Cache | HackerNoon](https://images.openai.com/static-rsc-4/wc_Pmm2llWuswePLwpS_Hk06VViFd-MqkcZ62WqXbA0YVU5CxPm_bOAoU8jJrYgXVUEMAbICKAwnY8-NRUKReJSvzDW5Lqr5GUd2-QTw0tVpv9qyl1wfmYLf6rs1oRYm2-VnsMRPhJtbc3tAeETDtjsG3pTqllWD6lEubO68R-I?purpose=inline)

```
Customer
   ↓
FastAPI
   ↓
Semantic Cache
   ↓
LangGraph
   ↓
Query Router
   ↓
Multi-Query Generation
   ↓
Vector Search + BM25
   ↓
RRF
   ↓
CrossEncoder
   ↓
Confidence Check
   ↓
Neo4j (when needed)
   ↓
LLM
   ↓
Grounded Answer
```

# Phase 1 — Basic RAG

### Problem

Customers ask questions like:

> "Can I choose my seat after booking?"

An LLM alone can hallucinate because it doesn't know HolidayBreakz policies.

### Solution

Build a Retrieval-Augmented Generation (RAG) system.

![Matt Pocock’s 5 Claude Code skills made me rewrite how I work with AI agents | by Aditya Kumar Puri | Medium](https://images.openai.com/static-rsc-4/frud46zwTGqtkosHZWnfCqH6m_F7mSzFbveqholbMUPKKXF68nRi3mLgxBTmcqQdMCv_-Qn1DXacswMbuZgHxm2KvM2lq5-SC7hU7XyiQ0-bTVKUSsJCXp-OZpcI7rjRGs-BvMT7DU2niWbXcNWIRoVLDRqN7zJTpBTKE7OriFw?purpose=inline)

Flow:

```
Question
   ↓
Vector Search
   ↓
Relevant Text
   ↓
LLM
   ↓
Answer
```

### Files

* `ingest.py`

* `retriever.py`

* Chroma DB

### Why Chroma?

Chroma stores embeddings.

Example:

KB says:

> Seat Selection

User asks:

> Choose my seat later

Semantic search still finds it.

### First Failure

Vector search sometimes missed exact product names.

Example:

```
Refund Shield
Cancellation Protection
```

These are proper nouns.

Vector similarity alone wasn't always enough.

# Phase 2 — BM25

![Ranking Documents with BM25-Understanding the Math Behind Search Relevance | by Spandana Doki | Medium](https://images.openai.com/static-rsc-4/uYNdlIv8JSFbAKNs3qhO83afCfSRn4r4h0oJIn0eyMLSuEa5b9qjTBuI6m2_pLsYGLmC6qXN3yfAwtEJhw41z-cJrG7LjkhBM5PXtyyK8aEkJZwKRBepUU9sgSX9Sgr0izVgx6tJrQkMtpUgTCGV6TgyTYKuTEHzi7FhvMS2T6k?purpose=inline)

### Problem

Exact words matter.

Example:

```
Refund Shield
```

should find:

```
Refund Shield
```

not generic refund text.

### Solution

Add BM25.

BM25 scores keyword overlap.

### Flow

```
Question
   ↓
BM25
   ↓
Keyword Matches
```

### Result

Now exact product names became easier to retrieve.

### Failure

Now two retrieval systems existed.

* Chroma

* BM25

Sometimes they disagreed.

# Phase 3 — Hybrid Retrieval

![Hybrid Search Done Right: Fixing RAG Retrieval Failures using BM25 + HNSW + Reciprocal Rank Fusion in Elasticsearch](https://images.openai.com/static-rsc-4/OH47I2_IWoTJWSd6tOdhgIylu9yiPlGFiI9wioC3MAs2ZoB5xNHHIoAD8PiqRyjmbJXboQJX8l_7nKwWDUKfGGlNY3TzJ7AAS9AEqGyPEF8Kzz0FQrwPNcR_wYNFb9suErtYYX9-E00Eh6WVaTpydJak2PPr_dmUnZm6s5kQiuQ?purpose=inline)

### Problem

Vector search and BM25 returned different rankings.

Example:

|
Vector

|

BM25

|
| --- | --- |
|

Seat

|

Refund Shield

|
|

Seat

|

Seat

|

Which ranking should we trust?

### Solution

Use Reciprocal Rank Fusion (RRF).

### Why RRF?

Instead of choosing one retriever,

combine both rankings.

Formula:

1k+rank\frac{1}{k+rank}k+rank1

High-ranked documents receive more weight.

### Flow

```
Vector
      \
       RRF
      /
BM25
```

### Result

Better recall.

### Failure

The correct chunk wasn't always ranked first.

# Phase 4 — CrossEncoder Reranker

![Fireworks AI](https://images.openai.com/static-rsc-4/ED-Mmi_693_LQ5j4s_HfrQfTOBCIjwIVAZ5lPKcsOmUGikregmq7WDw8jyeOP4eyZOuA0Ds8f9GKptjhQIxrsBa67p0uS87B38MZy-iPAjAlwiotB4TkOlgZvhEW4DdxGoGKTMh-cmzpm6n6RqhrisFun9wXW56ASp6oOjibpfQ?purpose=inline)

### Problem

Hybrid retrieval returned good candidates,

but their order wasn't always ideal.

Example:

Top results:

```
Seat

Seat Price

Seat Change

Seat Booking
```

The actual answer might be third.

### Solution

Add CrossEncoder.

Unlike embeddings,

CrossEncoder reads:

```
Question + Document
```

together.

Example:

```
Question:
Can I choose my seat later?

Document A:
Seat booking.

Score: 2.1

Document B:
Choose seat after booking.

Score: 8.7
```

Document B moves to the top.

### Result

Near-miss evaluation reached:

```
100%
```

after reranking.

# Phase 5 — Retrieval Evaluation

![Retrieval | Okareo Docs](https://images.openai.com/static-rsc-4/lOmkKACHuq70MQKWgtu-_C2s9YHJTyD7JeGAd1PjH1i9sW3AXiqYIdF9yWiJ5fb0HI1GULibV5Lx5zlcrb1RogSYIKibWaWLhaQiaYq2AD04Ayk6rDq5JTV3UHAlPyx8MvassL-AKpj_gV6C9IxUirtEeaDnO8Ge2gg68UijVck?purpose=inline)

### Problem

Improvements need measurement.

### Solution

Create evaluation datasets.

Metrics included:

* Recall@K

* Precision@K

* Hit Rate

* MRR

### Near-Miss Evaluation

Example:

Specific:

> Refund Shield

Generic:

> Refund

This tested whether retrieval confused similar concepts.

### Result

|
Method

|

Specific

|

Generic

|
| --- | --- | --- |
|

Vector

|

90%

|

60%

|
|

BM25

|

70%

|

80%

|
|

Hybrid

|

90%

|

90%

|
|

Reranked

|

100%

|

100%

|

### Why this matters

Interview answer:

> "I measured retrieval quality instead of assuming improvements."

# Phase 6 — Neo4j Graph RAG

![AI For Customer Experiences: A Retail Example - Developer Guides](https://images.openai.com/static-rsc-4/dR_IPjuqmvMANsga7HgfBBUiKcJJxT82LYpjgK7aOmOYUZl6BsDG_GSv5RwXqAB0otaRLFFjMA07hIv1qEMBR8s8PZa6r2o6Oar2fWn87MeFzTPMG2NGQo9P8WBRXCMb5iWeqHeZ8tLw6KCp2kwkCvzu503tW1pePdy6ay9zdvQ?purpose=inline)

### Problem

Some knowledge is relational.

Example:

```
Seat
   ↓
Window Seat

Seat
   ↓
Aisle Seat
```

Representing this as plain paragraphs isn't ideal.

### Solution

Create Neo4j.

Example graph:

```
Seat
 ├── Window
 ├── Aisle
 ├── Middle
 └── Extra Legroom
```

### Files

* `neo4j_graph.py`

* `neo4j_ingest.py`

* `graph_retriever.py`

### Example

Question:

> What seat options exist?

Graph returns:

```
Window

Aisle

Middle

Extra Legroom
```

### Failure

Initially,

Graph wasn't integrated into the main agent.

It worked separately.

# Phase 7 — Central Retrieval Pipeline

### Problem

Too many retrieval files existed.

```
retriever.py

graph_retriever.py

agent.py
```

Everything wasn't centralized.

### Solution

Create:

```
retrieval_pipeline.py
```

Now:

```
agent
 ↓
retrieval_pipeline
 ↓
retrievers
```

became cleaner.

# Phase 8 — Query Router

![Enterprise-Grade AI: A Visual Deep-Dive into Advanced Retrieval-Augmented Generation | by Jayita Bhattacharyya | Medium](https://images.openai.com/static-rsc-4/p_EmxlEcyrKUotLFTJqMbNiXBTUvOAKhypD5DrBUHBfSLXTESsExEb9kY3Qji5l68LRVGBAm4KviiIpotE8rahT6BViqv8jFmdTow2Cfh2Wg_PaNXrRezvcXA1OwMB85qS_Xo1DHhaOAkkXm7NMbB89vu3y6vamytcoxcFcnyjI?purpose=inline)

### Problem

Every question used every retriever.

Wasteful.

Example:

```
What seat options?
```

should use Graph.

Example:

```
Refund policy.
```

doesn't always need Graph.

### Solution

Router.

Routes:

```
RAG

Graph

Both
```

### Example

|
Question

|

Route

|
| --- | --- |
|

Seat options

|

Both

|
|

Graph relationships

|

Graph

|
|

General refund

|

RAG

|

### Why?

Faster.

Cleaner.

More efficient.

# Phase 9 — Semantic Cache

![Mastering Caching Methods in Large Language Models (LLMs)  | Medium](https://images.openai.com/static-rsc-4/KZ_Bqv6ze1WePb0unVfm4FnkqMhKhHoqBzrYXAIEVn8HuDoCzwkj6mKYlI_3GJ0ofKSEmcCOBjIAPtPE8RPVdHNLGQbz45gZjH1_X-7yL9-Bgln9WfyC1OJ_ff0I3nyzitfZ-6efl-_ZbHeRvCojtax1lAiAr-OgIlTXErWwY_I?purpose=inline)

### Problem

Repeated questions kept calling the LLM.

Example:

Two users ask:

> What is Refund Shield?

Same work repeated.

### Solution

SQLite semantic cache.

Flow:

```
Question
 ↓
Embedding
 ↓
Compare similarity
 ↓
Cache Hit?
```

If similarity ≥ threshold,

reuse the answer.

### Result

Faster responses.

Lower LLM cost.

# Phase 10 — Confidence Layer

![Building Advanced Query Engine and Evaluation with LlamaIndex and W\&B](https://images.openai.com/static-rsc-4/kiEDwRE1Mz-MW9cwZ9e-gphcbgz0TWlHAgB_CNy-1uIXgWzJxxzup7HvHgNZcva4dAg5uGufxDkD5RUGBDfrEp4ek9kD87yd_ggz8z1XwRWlbGLcbOgVbQEoA6ecp0bQ5fZLMJ8e61xWEEy4jQRyEAyYO1FyzdKe2TabhG9hTe0?purpose=inline)

### Biggest discovery

This happened during testing.

Question:

> What is the weather on Mars?

Old behavior:

```
Retrieved random HolidayBreakz text

HIGH confidence

Wrong.
```

### Why?

Context existed.

The system assumed:

```
Context exists

=

Good answer
```

That's false.

### Solution

Use CrossEncoder score.

Example:

|
Question

|

Score

|
| --- | --- |
|

Seat

|

2.827

|
|

Mars

|

-11.191

|

Threshold:

```
1.0
```

Now:

```
Score

↓

HIGH

↓

LLM
```

and

```
LOW

↓

Fallback
```

### Validation

10-question confidence dataset.

Result:

```
10/10 PASS
```

Relevant:

```
6/6
```

Unknown:

```
4/4
```

### Interview answer

> "I added a confidence layer before generation so weak retrieval doesn't reach the LLM."

# Phase 11 — Multi-Query Retrieval

![RAG Part III: The Intelligence of Retrieval | by Inkollu Sri Varsha | Jan, 2026 | Medium](https://images.openai.com/static-rsc-4/K_MRlX6SkDDcYqVL4JBMAwPtxayM49_EUrp93f40Swnjo1HNBeMX-smzVDHANWFzGHw-Y6Hs9uBfVLExqhUmaBgY_IXuFSZCouuuDKM9OgytvzG3JFzBIe_EjxikKZpprVdIGR8_KiHzw8zDnV1ioG-un6Oo72CGyS6jK_DMgzs?purpose=inline)

### Problem

Users use different wording.

Example:

KB:

> Seat Selection

User:

> Can I choose my seat later?

Different words.

Same meaning.

### Solution

Generate multiple search queries.

Example:

Original:

```
Can I choose my seat after booking?
```

Generated:

```
Select seat after reservation.

Pick seat after booking.

Seat selection post-booking.
```

Each query searches independently.

Then:

* Vector

* BM25

* RRF

* Reranker

### Result

Example score:

```
8.718
```

Correct seat chunk became the top result.

# LangGraph

![Building an Intelligent Q\&A System: Agentic RAG with LangChain, LangGraph, and GPT-4o-mini | by Aniket Mallick | Medium](https://images.openai.com/static-rsc-4/-5MGEtYUqy-MW72-C9XitNkQTW7fr9ZeTifiZ8psRrrm1N_Zm06TQOQJer3MFx2KeyADxHkfaEudW9qZT3rIjpUNTAvBFwQEF_ffjPrXT-JuI5wJYh2p_xKbLPqAYXzfhIhhBXZKvxIcolsK0Dpj55H9MfmVxTTzX9gm0Ey4PIA?purpose=inline)

### Why LangGraph?

Instead of one giant function,

split work into nodes.

Current nodes:

```
Retrieve

↓

LLM

↓

Fallback
```

Benefits:

* state

* checkpointing

* retries

* future expansion

SQLite stores checkpoints.

# Problems You Solved During Development

|
Problem

|

Fix

|
| --- | --- |
|

`.env` not loading

|

Corrected path

|
|

Neo4j URI missing

|

Fixed dotenv location

|
|

`rank_bm25` missing

|

Installed package

|
|

`sentence_transformers` missing

|

Installed package

|
|

`rag` import errors

|

Fixed Python path

|
|

Empty JSON

|

Added dataset

|
|

Cache returned old wrong answer

|

Tested with new thread/question

|
|

Router returning wrong route

|

Updated router logic

|
|

Graph separate from RAG

|

Built retrieval pipeline

|
|

Weak retrieval looked confident

|

Added confidence layer

|

These debugging stories are valuable interview examples because they show how you diagnosed and fixed integration problems.

# Current Tech Stack

|
Layer

|

Technology

|
| --- | --- |
|

API

|

FastAPI

|
|

Workflow

|

LangGraph

|
|

Vector DB

|

Chroma

|
|

Keyword Search

|

BM25

|
|

Fusion

|

RRF

|
|

Reranker

|

CrossEncoder

|
|

Graph

|

Neo4j

|
|

Cache

|

SQLite

|
|

LLM

|

OpenRouter

|
|

Evaluation

|

Recall, Precision, Hit Rate, MRR, Near-Miss, Confidence

|

This is the easiest way to remember it for interviews: every feature was added because the previous version had a problem. Think of it as a story where each improvement fixes one specific failure.

# Why we use every RAG component (Problem → Solution → Result)

![Hybrid Search Done Right: Fixing RAG Retrieval Failures using BM25 + HNSW + Reciprocal Rank Fusion in Elasticsearch](https://images.openai.com/static-rsc-4/tfjN9Wt5uxXYR_cP5eNpY2WcCKrVjOwcbcAnMwg-E3l_mSNllGKqbt8eotyvgn3K3eSEfJipjErBe9Wu1763JYPtCIgIwVrYHEaewcVUPdYmNYrj-g_Wv6jlvp3yIPfVLiMuKwqPFlJxbu47syF6KM2ZSJiqEXXad7X5WwI4i1c?purpose=inline)

## 1. Vector RAG — Find similar meaning

### Problem

The LLM doesn't know HolidayBreakz policies and may hallucinate.

Example:

> "Can I choose my seat later?"

The KB says "Seat Selection."

### Solution

Convert documents and the question into embeddings and search for similar meaning.

![🚀 Introduction to Vector Search | Sciences 44](https://images.openai.com/static-rsc-4/jBnmo8QWApqJ3fLA-dI5_J6xoczD8Or1G1WlH0VVkkeL9jWjbPA3ox0SixIcziDop1QRoBWf4y7u2Wrbr6uDK8G2mIJGwXUOtVx4TdM2n8hYbzuNX3pwMV6fsr6GTekZxwMRyiuJ1Y01SwgXgiJtfuym1FnAMhHNbgfcUphH9UI?purpose=inline)

```
Question
   ↓
Embedding
   ↓
Chroma
   ↓
Similar chunks
```

### Result

It finds related information even when the wording is different.

## 2. BM25 — Find exact words

### Problem

Vector search can miss proper names.

Example:

> Refund Shield

might retrieve a generic refund policy.

### Solution

BM25 searches using exact keywords.

![BM25 Explained: The Classic Algorithm that Still Powers Search Today | by Zawanah | Medium](https://images.openai.com/static-rsc-4/Hyed4LjhxWTNusZfK7QmSV2pzjPPRaLqJJIhz5QwM7XKo7sAWgs4JFUgyHeLYCP-JZT1tDtULAhDGnn8tciJTie60_c7bQrBMSipW4nn3EGsVDsHm1jp2zTp-vI8GLlnIxyNrXWlNh8xrvX-kL4K0lG-MO9KYcjdL5cTGk891sY?purpose=inline)

```
Refund Shield
      ↓
Exact keyword search
      ↓
Refund Shield chunk
```

### Result

Named products become much easier to find.

## 3. RRF — Combine both searches

### Problem

Now you have two retrievers.

* Vector says Document A.

* BM25 says Document B.

Which one should you trust?

### Solution

Use Reciprocal Rank Fusion (RRF).

![Building RAG: All things retrieval | Gen-AI](https://images.openai.com/static-rsc-4/4--VABn0PfisVzpFNLx_tbdHRti6ky4kzC8X_4cy3jBaYjpgYwIkjrqJF0H7Ym0xof1J4ohzZZ2cZPiHQuxZiFX9MPTNX6UiNHgIeZGcV5S7NM59KgvBw8ALvI1kJ6CfPr1bcn7Mz6Wl1xlyeeKDGAk_eHvCrm2Uyh50sfj2TEA?purpose=inline)

Instead of choosing one, combine both rankings.

```
Vector
      \
       RRF
      /
BM25
```

### Result

Better recall because both retrieval methods contribute.

## 4. CrossEncoder — Put the best answer first

### Problem

RRF finds good candidates, but the best one isn't always first.

Example:

```
Seat Booking
Seat Price
Choose Seat After Booking
```

The third document is actually the answer.

### Solution

CrossEncoder reads:

```
Question + Document
```

together and gives each document a relevance score.

![Using a cross encoder model to re-rank retrieved results is a practical way to improve your RAG pipeline!
In our upcoming RAG workshop I'll talk about:
🔹how cross-encoders work
🔹where to add them… | Zain Hasan](https://images.openai.com/static-rsc-4/0OvTSAxWDNOhCrd6hnGjg7k0kNLeljhq9oHle5WSvZ30DGqmsfefwvsuKP624XUs952zIcakGqLZxp5IdsM-UNZh_pIT5KPkNkBGfay2w8FoBgL7uATOGrNTTeE59p0AGSdoox7SU5IwSz0Xe68LgwHt6EqY0lx6SNuYlqC6ZHE?purpose=inline)

Example:

|
Document

|

Score

|
| --- | --- |
|

Seat Booking

|

2.1

|
|

Choose Seat After Booking

|

8.7

|

### Result

The correct chunk moves to the top.

## 5. Evaluation Dataset — Prove improvements

### Problem

You can't just say,

> "It feels better."

### Solution

Create test questions and measure retrieval.

![Retrieval | Okareo Docs](https://images.openai.com/static-rsc-4/lOmkKACHuq70MQKWgtu-_C2s9YHJTyD7JeGAd1PjH1i9sW3AXiqYIdF9yWiJ5fb0HI1GULibV5Lx5zlcrb1RogSYIKibWaWLhaQiaYq2AD04Ayk6rDq5JTV3UHAlPyx8MvassL-AKpj_gV6C9IxUirtEeaDnO8Ge2gg68UijVck?purpose=inline)

Metrics:

* Recall

* Precision

* Hit Rate

* MRR

* Near-Miss

Example:

|
Method

|

Generic

|
| --- | --- |
|

Vector

|

60%

|
|

Hybrid

|

90%

|
|

Reranked

|

100%

|

### Result

Now every improvement is backed by numbers.

## 6. Neo4j Graph RAG — Store relationships

### Problem

Some knowledge isn't just text.

Example:

```
Seat
   ↓
Window Seat
```

That's a relationship.

### Solution

Store entities as a graph.

![AI For Customer Experiences: A Retail Example - Developer Guides](https://images.openai.com/static-rsc-4/dR_IPjuqmvMANsga7HgfBBUiKcJJxT82LYpjgK7aOmOYUZl6BsDG_GSv5RwXqAB0otaRLFFjMA07hIv1qEMBR8s8PZa6r2o6Oar2fWn87MeFzTPMG2NGQo9P8WBRXCMb5iWeqHeZ8tLw6KCp2kwkCvzu503tW1pePdy6ay9zdvQ?purpose=inline)

```
Seat
 ├── Window
 ├── Aisle
 ├── Middle
 └── Extra Legroom
```

### Result

Relationship questions become easier.

Example:

> "What seat options are connected?"

## 7. Query Router — Don't use every retriever every time

### Problem

Every question was using every retrieval system.

Wasteful.

### Solution

Route questions.

![Beyond Basic RAG: Mastering Routing, Query Construction, and Advanced Retrieval — part 2 | by Tejpal Kumawat | Medium](https://images.openai.com/static-rsc-4/-VWT35bV9--FLdo2n039_dhmonHjRhTJwYunN-hZDsOW07G2FK4JI7_WiPWIDB7P5T1Boocuo0ZA9YdD2tIwYw1t0RBVC3OEK-n3gNo_Im7vaAB_b1mS7TFGSyF6fD_BN8LSX9NHMSDihNIkG0ORkLfiGaC8tBQrGVyjEA38uh0?purpose=inline)

```
Question
   ↓
Router
   ↓
RAG / Graph / Both
```

Examples:

|
Question

|

Route

|
| --- | --- |
|

Refund

|

RAG

|
|

Seat Options

|

Both

|
|

Graph Relationship

|

Graph

|

### Result

Cleaner and faster.

## 8. Semantic Cache — Don't repeat expensive work

### Problem

The same question keeps calling the LLM.

Example:

> "What is Refund Shield?"

asked repeatedly.

### Solution

Store:

* question embedding

* answer

![Mastering Caching Methods in Large Language Models (LLMs)  | Medium](https://images.openai.com/static-rsc-4/KZ_Bqv6ze1WePb0unVfm4FnkqMhKhHoqBzrYXAIEVn8HuDoCzwkj6mKYlI_3GJ0ofKSEmcCOBjIAPtPE8RPVdHNLGQbz45gZjH1_X-7yL9-Bgln9WfyC1OJ_ff0I3nyzitfZ-6efl-_ZbHeRvCojtax1lAiAr-OgIlTXErWwY_I?purpose=inline)

```
Question
   ↓
Embedding
   ↓
Similarity Check
   ↓
Cache Hit
```

### Result

* Faster

* Cheaper

* Lower API usage

## 9. Confidence Layer — Stop hallucinations

### Biggest problem

You tested:

> "What is the weather on Mars?"

Old system:

* retrieved random HolidayBreakz text

* answered anyway

Wrong.

### Solution

Use the CrossEncoder score.

![Building Advanced Query Engine and Evaluation with LlamaIndex and W\&B](https://images.openai.com/static-rsc-4/kiEDwRE1Mz-MW9cwZ9e-gphcbgz0TWlHAgB_CNy-1uIXgWzJxxzup7HvHgNZcva4dAg5uGufxDkD5RUGBDfrEp4ek9kD87yd_ggz8z1XwRWlbGLcbOgVbQEoA6ecp0bQ5fZLMJ8e61xWEEy4jQRyEAyYO1FyzdKe2TabhG9hTe0?purpose=inline)

Example:

|
Question

|

Score

|
| --- | --- |
|

Seat

|

2.827

|
|

Mars

|

-11.191

|

Threshold:

```
1.0
```

Now:

```
Score High
     ↓
LLM

Score Low
     ↓
Fallback
```

### Result

Unknown questions no longer generate grounded-looking wrong answers.

## 10. Multi-Query Retrieval — Understand different wording

### Problem

Different users ask the same thing differently.

Examples:

* Can I choose my seat later?

* Pick my seat after booking?

* Seat selection post-booking?

Same meaning.

### Solution

Generate multiple search queries.

![RAG Part III: The Intelligence of Retrieval | by Inkollu Sri Varsha | Jan, 2026 | Medium](https://images.openai.com/static-rsc-4/K_MRlX6SkDDcYqVL4JBMAwPtxayM49_EUrp93f40Swnjo1HNBeMX-smzVDHANWFzGHw-Y6Hs9uBfVLExqhUmaBgY_IXuFSZCouuuDKM9OgytvzG3JFzBIe_EjxikKZpprVdIGR8_KiHzw8zDnV1ioG-un6Oo72CGyS6jK_DMgzs?purpose=inline)

```
Original Question
        ↓
Generate 3 variations
        ↓
Search each
        ↓
Merge results
        ↓
Rerank
```

Your test:

```
Can I choose my seat after booking?
```

became

* select my seat after reservation

* pick my seat following my booking

* select a seat post-booking

Best reranker score:

```
8.718
```

### Result

Higher chance of finding the correct chunk even when wording changes.

