# HolidayBreakz Customer Support AI

## Complete Project Explanation — Architecture, Features, Failures, Learnings & Next Steps

---

# 1. PROJECT OVERVIEW

I built **HolidayBreakz Customer Support AI**, an AI-powered customer-support assistant designed to answer customer questions using the company's knowledge base.

The main objective was:

> **Generate grounded customer-support answers while reducing hallucinations.**

Instead of directly sending a customer question to an LLM, I created a retrieval-first architecture:

```text
Customer Question
       ↓
Retrieve relevant information
       ↓
Rank / validate information
       ↓
Provide context to LLM
       ↓
Generate grounded answer
```

The project gradually evolved from basic RAG into a more advanced retrieval architecture:

```text
Basic RAG
   ↓
Vector RAG
   ↓
Hybrid RAG
   ↓
RRF
   ↓
CrossEncoder Reranking
   ↓
Graph RAG with Neo4j
   ↓
Evaluation
   ↓
Semantic Cache
   ↓
LangGraph orchestration
   ↓
Production-oriented architecture
```

---

# 2. PROBLEM STATEMENT

A normal LLM can generate an answer that sounds correct even when that information does not exist in the company's knowledge base.

For a travel-support application, this can be problematic.

Customers may ask:

```text
What seat options are available?

How much does baggage cost?

Can I add baggage after booking?

What is Refund Shield?

What does Refund Shield cover?

How do I use Cancellation Protection?

What is the baggage policy for connecting flights?

What should I do for a multi-airline itinerary?
```

The assistant therefore needs to retrieve relevant company information before generating an answer.

My core principle was:

```text
Retrieve first
Generate second
```

instead of:

```text
Ask LLM directly
      ↓
Hope the answer is correct
```

---

# 3. TECHNOLOGY STACK

## Backend

```text
Python
FastAPI
```

## AI / LLM

```text
LangChain
LangGraph
OpenRouter
GPT-4o-mini
```

## Retrieval

```text
Chroma
BM25
RRF
CrossEncoder
```

## Knowledge Graph

```text
Neo4j Aura
Cypher
```

## Persistence

```text
SQLite
LangGraph checkpointing
Semantic cache
```

## Frontend

```text
React
Vite
```

## Development

```text
Git
GitHub
Environment variables
```

## Planned production technologies

```text
PostgreSQL
Docker
Monitoring
Authentication
Business APIs
MCP
```

---

# 4. HIGH-LEVEL ARCHITECTURE

My current architecture is:

```text
                         USER
                           │
                           ▼
                       React UI
                           │
                           ▼
                        FastAPI
                           │
                           ▼
                    Semantic Cache
                           │
                    Cache Hit?
                    ┌──────┴──────┐
                    │             │
                   YES            NO
                    │             │
                    ▼             ▼
                 Answer       LangGraph
                                  │
                     ┌────────────┴────────────┐
                     │                         │
                     ▼                         ▼
                Hybrid RAG                  Neo4j
                     │                    Graph Retrieval
              ┌──────┴──────┐                 │
              │             │                 │
           Chroma          BM25               │
              │             │                 │
              └──────┬──────┘                 │
                     ▼                        │
                    RRF                       │
                     │                        │
                     ▼                        │
                CrossEncoder                  │
                 Reranker                     │
                     │                        │
                     └──────────┬─────────────┘
                                ▼
                        Combined Context
                                │
                                ▼
                               LLM
                                │
                                ▼
                             Answer
                                │
                                ▼
                          Save to Cache
```

---

# 5. COMPLETE REQUEST FLOW

Example question:

```text
What seat options can I select?
```

The request goes through:

```text
User
 ↓
React
 ↓
FastAPI
 ↓
Semantic Cache
 ↓
Cache Miss
 ↓
LangGraph
 ↓
Hybrid Retrieval
 ↓
Chroma + BM25
 ↓
RRF
 ↓
CrossEncoder Reranker
 ↓
Neo4j Graph Retrieval
 ↓
Combine Context
 ↓
LLM
 ↓
Grounded Answer
 ↓
Save Answer in Cache
 ↓
User
```

---

# 6. KNOWLEDGE BASE

I created a knowledge base containing HolidayBreakz customer-support information.

Major topics include:

```text
Seat
Baggage
Meal
Cancellation Protection
Refund Shield
Connecting Flights
Multi-Airline Itineraries
Refund Rules
Price Rules
Fallback Rules
```

The knowledge base was split into smaller chunks before being indexed.

I assigned stable IDs:

```text
kb_000
kb_001
kb_002
...
kb_041
```

These IDs became very useful later when debugging retrieval and evaluating the system.

---

# 7. DOCUMENT CHUNKING

I used:

```text
RecursiveCharacterTextSplitter
```

with approximately:

```text
chunk_size = 700
chunk_overlap = 100
```

The overlap helps prevent important information from being lost at chunk boundaries.

For example:

```text
Chunk 1
-------------------------
Seat selection
Seat options
Seat pricing
-------------------------

Chunk 2
-------------------------
Seat pricing
Seat confirmation
Seat changes
-------------------------
```

The repeated information between chunks helps preserve context.

---

# 8. CHROMA VECTOR SEARCH

I used Chroma as the vector store.

The process is:

```text
Knowledge Base
      ↓
Chunking
      ↓
Embeddings
      ↓
Chroma
```

When the customer asks a question:

```text
Question
   ↓
Embedding
   ↓
Similarity Search
   ↓
Relevant Chunks
```

Vector search is useful because it can understand semantic similarity.

For example:

```text
"Can I select an aisle?"

```

can retrieve information about:

```text
Aisle Seat
Seat Options
Seat Selection
```

even when the exact wording is different.

---

# 9. FIRST IMPORTANT LIMITATION — VECTOR SEARCH

One of my important learnings was:

> **Vector search alone is not enough for every type of customer-support question.**

For example, the knowledge base contains specific product names:

```text
Refund Shield
Cancellation Protection
```

These exact terms can be very important.

Semantic search may retrieve related refund or cancellation information without necessarily putting the exact requested clause at the top.

That led me to BM25.

---

# 10. BM25

I added BM25 keyword retrieval.

BM25 is useful when exact terms matter.

For example:

```text
"What is Refund Shield?"
```

The phrase:

```text
Refund Shield
```

is an important lexical signal.

So:

```text
Vector Search
= semantic similarity

BM25
= keyword / lexical matching
```

The two approaches complement each other.

---

# 11. HYBRID RETRIEVAL

Instead of choosing between vector search and BM25, I combined them.

Architecture:

```text
                    Question
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
        Vector Search          BM25
             │                   │
             ▼                   ▼
        Vector Ranking       Keyword Ranking
             │                   │
             └─────────┬─────────┘
                       ▼
                      RRF
                       │
                       ▼
                Hybrid Ranking
```

---

# 12. RRF — RECIPROCAL RANK FUSION

Vector and BM25 return different rankings.

Example:

```text
Vector:

kb_005 → Rank 1
kb_002 → Rank 2
kb_009 → Rank 3
```

BM25:

```text
kb_002 → Rank 1
kb_008 → Rank 2
kb_005 → Rank 3
```

Rather than choosing one ranking, I combine them using Reciprocal Rank Fusion.

The basic formula is:

```text
RRF Score = 1 / (k + rank)
```

I used:

```text
k = 60
```

A document that appears highly in multiple rankings receives a stronger combined score.

---

# 13. SECOND IMPORTANT LIMITATION — HYBRID RETRIEVAL

After adding BM25 + RRF, retrieval became more robust.

But I noticed another problem:

> The top candidates were not always in the best final order.

The correct document might be present in the candidate set but not ranked first.

That led to CrossEncoder reranking.

---

# 14. CROSSENCODER RERANKER

The architecture became:

```text
Question
   ↓
Vector Search
   +
BM25
   ↓
RRF
   ↓
Top Candidates
   ↓
CrossEncoder
   ↓
Final Ranking
```

The CrossEncoder receives:

```text
Question + Document
```

as a pair.

It then calculates a relevance score.

This allows it to judge the relationship between the exact customer question and each candidate document.

---

# 15. WHY RERANKING?

Imagine:

```text
Hybrid Retrieval:

kb_034
kb_036
kb_031
kb_033
```

The correct answer might be:

```text
kb_036
```

The reranker can move it to:

```text
kb_036
kb_031
kb_033
kb_034
```

This is second-stage retrieval.

The first stage finds candidates.

The second stage improves ordering.

---

# 16. RETRIEVAL EVALUATION

I did not want to simply assume that the retrieval system was working.

So I created an evaluation dataset.

Each question contains expected relevant chunk IDs.

Example:

```json
{
  "question": "How can I add baggage after booking?",
  "relevant_chunk_ids": ["kb_012"]
}
```

Then I compare:

```text
Expected Chunks
       vs
Retrieved Chunks
```

---

# 17. METRICS

I implemented:

```text
Recall@4
Precision@4
Hit Rate@4
MRR
```

### Recall@4

Measures how much of the relevant information was retrieved.

```text
Relevant retrieved
-------------------
All relevant
```

### Precision@4

Measures how many of the retrieved results were relevant.

```text
Relevant retrieved
-------------------
Total retrieved
```

### Hit Rate@4

Checks whether at least one relevant chunk appears in the top 4.

```text
Found → 1
Not found → 0
```

### MRR

Measures the rank of the first relevant result.

```text
Rank 1 → 1.00
Rank 2 → 0.50
Rank 3 → 0.33
Rank 4 → 0.25
```

---

# 18. MY FIRST EVALUATION FAILURE

This was an important learning.

Initially, my evaluation dataset contained some incorrect ground-truth chunk IDs.

That meant the evaluation was measuring the system against the wrong answer.

For example, a refund-related question was associated with an unrelated chunk.

The retrieval system could retrieve the correct information but still be marked as incorrect.

I realized:

```text
Bad ground truth
      ↓
Bad evaluation
      ↓
Misleading conclusions
```

So I corrected the ground-truth dataset.

This taught me:

> **Before optimizing retrieval, make sure the evaluation dataset itself is trustworthy.**

---

# 19. NEAR-MISS EVALUATION

I then created a separate near-miss evaluation.

The purpose was to test questions that are similar in meaning but require different information.

Example:

```text
Specific:
What is Refund Shield?

Generic:
How can I request a refund?
```

These questions are related, but they should not necessarily retrieve the same chunks.

Another example:

```text
Specific:
What is Cancellation Protection?

Generic:
Can I cancel an ancillary?
```

This tests whether the retrieval system can distinguish similar topics.

---

# 20. NEAR-MISS RESULTS

My current small near-miss dataset contains:

```text
10 specific questions
10 generic questions
```

The results were:

```text
                    Specific       Generic

Vector              90%            60%

BM25                70%            80%

Hybrid RRF          90%            90%

Hybrid + Reranker   100%           100%
```

These are **small test-set results**, not a production accuracy claim.

The important learning was:

```text
Vector
→ good semantic understanding

BM25
→ good exact terminology

Hybrid
→ combines both signals

Reranker
→ improves final relevance ordering
```

---

# 21. NEO4J — WHY I ADDED A GRAPH

I then asked:

> What if the information is not primarily about similar text, but about relationships?

For example:

```text
Seat
 │
 ├── HAS_OPTION → Window Seat
 ├── HAS_OPTION → Aisle Seat
 ├── HAS_OPTION → Middle Seat
 └── HAS_OPTION → Extra Legroom
```

Or:

```text
Baggage
 │
 ├── HAS_RULE → Connecting Flight
 └── HAS_RULE → Airline Specific
```

Or:

```text
Refund Shield
 │
 └── COVERS → Medical Reason
```

This information is naturally represented as a graph.

So I added Neo4j.

---

# 22. NEO4J KNOWLEDGE GRAPH

My Neo4j graph contains entities such as:

```text
Seat
Baggage
Meal
Cancellation Protection
Refund Shield
```

and connected entities such as:

```text
Window Seat
Aisle Seat
Middle Seat
Extra Legroom
Connecting Flight
Airline Specific
Medical Reason
Travel Disruption
```

Relationships include:

```text
HAS_OPTION
HAS_RULE
COVERS
```

---

# 23. WHY NEO4J?

Vector retrieval asks:

```text
What text is semantically similar?
```

Graph retrieval asks:

```text
What is connected to this entity?
```

For example:

```text
What options are available for Seat?
```

Neo4j can directly traverse:

```text
Seat
 ↓
HAS_OPTION
 ↓
Window Seat
Aisle Seat
Middle Seat
Extra Legroom
```

This makes graph retrieval useful for relationship-heavy questions.

---

# 24. GRAPH RETRIEVER

I created graph retrieval logic.

The system identifies known entities such as:

```text
Seat
Baggage
Meal
Cancellation Protection
Refund Shield
```

Then it queries Neo4j using Cypher.

Example:

```text
Question:
What seat options are available?
```

Entity:

```text
Seat
```

Graph query:

```text
Seat
 ↓
HAS_OPTION
 ↓
Options
```

Result:

```text
Seat HAS_OPTION Window Seat
Seat HAS_OPTION Aisle Seat
Seat HAS_OPTION Middle Seat
Seat HAS_OPTION Extra Legroom
```

---

# 25. THIRD IMPORTANT LIMITATION — GRAPH RAG

The first version of my Graph RAG was fairly simple.

It mainly relied on known entity detection.

For example:

```text
"seat"
→ Seat

"baggage"
→ Baggage

"refund shield"
→ Refund Shield
```

This works for known entities.

But a production system needs to understand:

```text
What is the entity?
What is the user's intent?
Does the question require text retrieval?
Does it require graph retrieval?
Does it require both?
```

That is why query routing is my next improvement.

---

# 26. RAG + GRAPH RAG

I combined the two sources.

```text
                    QUESTION
                        │
             ┌──────────┴──────────┐
             ▼                     ▼
        Hybrid RAG              Neo4j
             │                  Graph
             ▼                     │
      Textual Context       Relationship Context
             │                     │
             └──────────┬──────────┘
                        ▼
                 Combined Context
                        │
                        ▼
                       LLM
```

The LLM receives both forms of information.

---

# 27. RETRIEVAL PIPELINE

To avoid duplicating retrieval logic inside the agent, I created a centralized retrieval pipeline.

Conceptually:

```text
retrieval_pipeline.py
        │
        ├── retrieve_context()
        │      │
        │      ├── Vector
        │      ├── BM25
        │      ├── RRF
        │      └── Reranker
        │
        └── Graph Retriever
               │
               └── Neo4j
```

This gives the project a cleaner separation of responsibilities.

---

# 28. LANGGRAPH

I use LangGraph to orchestrate the workflow.

Instead of putting everything into one large function, the workflow is divided into nodes.

Current simplified flow:

```text
START
  ↓
Retrieve
  ↓
LLM
  ↓
END
```

The retrieve node gets:

```text
Hybrid RAG context
+
Neo4j graph context
```

The LLM node generates the response using that context.

---

# 29. WHY LANGGRAPH?

I chose LangGraph because I wanted an explicit, stateful workflow.

As the project grows, I can extend it to:

```text
START
 ↓
Query Router
 ↓
 ┌─────────────┬──────────────┐
 ↓             ↓              ↓
RAG Agent   Graph Agent    Tool Agent
 ↓             ↓              ↓
Chroma      Neo4j          APIs
 └─────────────┴──────────────┘
               ↓
             LLM
               ↓
             Answer
```

LangGraph also provides checkpointing and state management.

---

# 30. SQLITE CHECKPOINTING

I used SQLite with LangGraph checkpointing.

The purpose is to persist workflow state associated with a conversation/thread.

Conceptually:

```text
Thread ID
    ↓
LangGraph
    ↓
Checkpoint
    ↓
SQLite
```

For example:

```text
thread_id = customer_123
```

can be associated with a conversation workflow.

For production, I would move this persistence layer to PostgreSQL.

---

# 31. SEMANTIC CACHE

I also added semantic caching.

Without caching:

```text
Question
 ↓
Retrieval
 ↓
LLM
 ↓
Answer
```

If the customer asks a very similar question again, we may unnecessarily call the LLM again.

With semantic caching:

```text
Question
 ↓
Embedding
 ↓
Cache Search
 ↓
Similar Answer?
 ├── YES → Return cached answer
 │
 └── NO
       ↓
    Retrieval
       ↓
      LLM
       ↓
   Save Answer
```

The cache uses semantic similarity rather than only exact string matching.

Potential benefits:

```text
Lower latency
Fewer LLM calls
Lower cost
```

---

# 32. IMPORTANT CACHE DEBUGGING LESSON

During testing, I saw something like:

```text
CACHE MISS
similarity = ...
Answer saved to semantic cache.
```

and the agent returned the fallback answer.

This initially looked like a cache problem.

But the actual issue was that retrieval had failed or returned no useful context.

The cache itself was functioning.

This taught me to debug systems layer by layer:

```text
Cache
 ↓
Retrieval
 ↓
Graph
 ↓
LLM
```

rather than assuming the first visible problem is the root cause.

---

# 33. FASTAPI

FastAPI is my backend API layer.

The simplified request flow is:

```text
React
 ↓
POST /chat
 ↓
FastAPI
 ↓
LangGraph
 ↓
Retrieval
 ↓
LLM
 ↓
Response
 ↓
React
```

I also have a health endpoint for checking backend availability.

---

# 34. OPENROUTER

I use OpenRouter as the LLM API layer.

The model and API credentials are configured through environment variables.

For example:

```text
OPENROUTER_API_KEY
OPENROUTER_MODEL
```

This avoids hardcoding secrets in source code.

---

# 35. HALLUCINATION CONTROL

One of the most important design goals was grounding.

The system prompt instructs the LLM to:

```text
Use only HolidayBreakz knowledge.

Do not invent information.

Do not assume missing information.

If the answer is not available,
ask the customer to contact HolidayBreakz support.
```

The principle is:

```text
Retrieved evidence
       ↓
LLM
       ↓
Answer
```

rather than:

```text
LLM
 ↓
Guess
```

---

# 36. FALLBACK

If the system cannot retrieve useful information, it should not invent an answer.

The fallback is:

```text
Please contact HolidayBreakz support for the most accurate information.
```

This is important for unknown questions.

---

# 37. RETRY / ERROR HANDLING

The LLM node has LangGraph retry configuration.

Conceptually:

```text
LLM
 ↓
Failure?
 ↓
Retry
 ↓
Retry
 ↓
Retry
 ↓
Fallback
```

The retrieval node also has exception handling.

For production I would additionally add:

```text
Timeouts
Rate limiting
Structured logging
Circuit breakers
Provider fallback
Monitoring
```

---

# 38. FRONTEND

The frontend uses:

```text
React
Vite
```

It provides a customer-support chat experience.

The frontend communicates with FastAPI rather than directly calling the LLM.

This keeps credentials and backend logic on the server side.

---

# 39. VOICE SUPPORT

The frontend also supports browser speech functionality.

Flow:

```text
Customer speaks
 ↓
Speech Recognition
 ↓
Text
 ↓
FastAPI
 ↓
AI Agent
 ↓
Text Answer
 ↓
Speech Synthesis
 ↓
Customer hears response
```

---

# 40. GITHUB

I manage the project using Git/GitHub.

The latest major retrieval work was committed and pushed.

Latest commit:

```text
2c44d3b
```

Commit message:

```text
Add hybrid RAG reranking Neo4j Graph RAG and near-miss evaluation
```

The project repository is:

```text
github.com/priyadixit123/Customer_SupportRAG
```

Sensitive environment files are excluded through `.gitignore`.

I also deliberately did not commit a local Neo4j certificate file.

---

# 41. MY MAJOR FAILURES / CHALLENGES

## Failure 1 — Vector retrieval was not enough

Problem:

```text
Semantic search
↓
Related content
↓
Not always exact content
```

Solution:

```text
BM25
+
Vector Search
```

---

## Failure 2 — Hybrid ranking was not always optimal

Problem:

```text
Correct document existed
but wasn't always ranked highest.
```

Solution:

```text
CrossEncoder reranking
```

---

## Failure 3 — Ground-truth evaluation was initially wrong

Problem:

```text
Wrong expected chunk IDs
        ↓
Misleading metrics
```

Solution:

```text
Inspect KB chunks
Correct ground truth
Expand evaluation dataset
```

Lesson:

> **Evaluation quality is as important as retrieval quality.**

---

## Failure 4 — Near-miss cases exposed retrieval weaknesses

Some questions were semantically close but needed different chunks.

Example:

```text
Refund Shield
vs
Generic Refund
```

This showed why:

```text
Vector
+
BM25
+
Reranker
```

are complementary.

---

## Failure 5 — Graph retrieval initially required known entities

Problem:

```text
Known entity
      ↓
Graph lookup
```

This works, but is limited.

Future improvement:

```text
Question
 ↓
Entity extraction
 ↓
Intent detection
 ↓
Query routing
 ↓
Cypher / Retrieval
```

---

## Failure 6 — Import/path problem during evaluation

When I first ran:

```text
python evaluation\evaluate_near_miss.py
```

I got:

```text
ModuleNotFoundError:
No module named 'rag'
```

The issue was the Python import path when running the evaluator from the `evaluation` directory context.

I fixed it by explicitly adding the backend directory to `sys.path`.

After that, the evaluator ran successfully.

This was a useful Python project-structure lesson:

```text
File location
        +
Python import path
        +
Package structure
```

all matter when running scripts.

---

## Failure 7 — Missing dependency

The reranker initially failed because:

```text
sentence_transformers
```

was not installed.

I installed the dependency and verified:

```text
CrossEncoder
```

could load successfully.

This reminded me that ML applications often have additional runtime dependencies beyond the main framework.

---

## Failure 8 — Neo4j certificate issue

The initial secure Neo4j connection had a certificate trust problem.

The connection failed with certificate verification.

For development, I used:

```text
neo4j+ssc
```

to establish the connection.

The connection was then successfully tested.

For production, I would use proper certificate validation rather than relying on a relaxed development configuration.

---

# 42. WHAT I LEARNED FROM THESE FAILURES

My biggest learning was that building an AI system is not only about writing the LLM prompt.

There are many layers:

```text
Data
 ↓
Chunking
 ↓
Embedding
 ↓
Retrieval
 ↓
Ranking
 ↓
Graph
 ↓
Workflow
 ↓
LLM
 ↓
Caching
 ↓
Evaluation
 ↓
Production
```

A failure at any layer can affect the final answer.

I also learned:

```text
Don't blindly trust retrieval.

Measure it.

Don't blindly trust evaluation.

Validate the ground truth.

Don't blindly trust the LLM.

Ground it with evidence.
```

---

# 43. MY BIGGEST TECHNICAL CHALLENGE

The biggest technical challenge was **retrieval quality**.

Initially I had:

```text
Question
 ↓
Vector Search
 ↓
LLM
```

But different questions need different retrieval signals.

So I gradually built:

```text
Vector
   +
BM25
   ↓
RRF
   ↓
CrossEncoder
   +
Neo4j
   ↓
Combined Context
   ↓
LLM
```

This was the biggest evolution of the project.

---

# 44. WHAT I CONTRIBUTED

My work covered the AI retrieval and agent workflow.

I worked on:

```text
Knowledge-base preparation
Document chunking
Stable chunk IDs
Chroma retrieval
BM25 retrieval
Hybrid retrieval
RRF
CrossEncoder reranking
Retrieval evaluation
Near-miss evaluation
Neo4j graph
Graph retrieval
RAG + Graph RAG
LangGraph workflow
SQLite checkpointing
Semantic caching
FastAPI integration
OpenRouter integration
Frontend/API integration
Fallback handling
Retry handling
Git/GitHub
```

My main focus was:

> **Improving retrieval quality and building a structured AI-agent workflow.**

---

# 45. CURRENT PROJECT STATUS

The current project demonstrates:

```text
✓ Knowledge-base RAG
✓ Chroma
✓ BM25
✓ Hybrid retrieval
✓ RRF
✓ CrossEncoder reranking
✓ Retrieval evaluation
✓ Near-miss evaluation
✓ Neo4j
✓ Graph retrieval
✓ RAG + Graph RAG
✓ LangGraph
✓ SQLite checkpointing
✓ Semantic cache
✓ FastAPI
✓ OpenRouter
✓ React
✓ Vite
✓ Voice support
✓ Fallback
✓ Retry handling
✓ Environment configuration
✓ GitHub
```

---

# 46. WHAT IS NEXT?

The next major improvement should be **Query Routing**.

Currently:

```text
Question
 ↓
Hybrid RAG
 +
Graph Retrieval
```

I want to make the system more intelligent:

```text
                    QUESTION
                       │
                       ▼
                  QUERY ROUTER
                       │
          ┌────────────┼────────────┐
          │            │            │
          ▼            ▼            ▼
       RAG only     Graph only    Both
          │            │            │
          ▼            ▼            ▼
      Chroma +      Neo4j        RAG +
        BM25                       Neo4j
          │            │            │
          └────────────┼────────────┘
                       ▼
                    Reranker
                       ↓
                      LLM
```

This can reduce unnecessary retrieval and make the architecture more efficient.

---

# 47. BETTER GRAPH RAG

Next I want to improve Graph RAG:

```text
Question
 ↓
Entity Extraction
 ↓
Intent Detection
 ↓
Graph Query
 ↓
Neo4j
 ↓
Graph Context
```

For example:

```text
"What options are available for seats?"
```

becomes:

```text
Entity = Seat
Intent = Find Options
```

Then the graph query retrieves:

```text
Seat → HAS_OPTION → ...
```

---

# 48. UNKNOWN-QUESTION EVALUATION

I also want to create a separate failure dataset.

Examples:

```text
Do you provide hotel discounts?

Can you book a taxi for me?

What is the weather in Dubai?

Do you offer travel insurance?
```

These may not exist in the current knowledge base.

The goal is to verify that the system:

```text
Doesn't hallucinate
        ↓
Recognizes missing knowledge
        ↓
Uses fallback
```

---

# 49. LARGER EVALUATION

The current near-miss dataset is intentionally small.

The next step is to increase the evaluation dataset.

I would include:

```text
Normal questions
Near-miss questions
Exact-term questions
Multi-intent questions
Ambiguous questions
Unknown questions
Out-of-domain questions
```

Then measure:

```text
Recall@K
Precision@K
Hit Rate@K
MRR
```

and generation-level metrics such as:

```text
Faithfulness
Answer relevance
Context relevance
Groundedness
```

---

# 50. MULTI-AGENT ARCHITECTURE

After routing is stable, I can introduce multi-agent architecture.

Example:

```text
                     SUPERVISOR
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
      RAG Agent      Graph Agent     Tool Agent
          │              │              │
       Chroma          Neo4j        Business APIs
       BM25
```

The Supervisor determines which agent should handle the request.

---

# 51. TOOL CALLING

The next step after knowledge retrieval is taking actions.

Potential tools:

```text
Booking API
Flight Search API
Refund API
Customer API
Payment API
Notification API
```

Then the architecture becomes:

```text
User
 ↓
Supervisor
 ↓
Agent
 ↓
Tool
 ↓
Business API
 ↓
Result
 ↓
LLM
 ↓
User
```

---

# 52. HUMAN-IN-THE-LOOP

For high-impact operations such as:

```text
Refund
Cancellation
Booking modification
Payment operations
```

I would add human approval.

Example:

```text
User
 ↓
Agent
 ↓
Action detected
 ↓
Human approval
 ↓
Business API
 ↓
Result
 ↓
User
```

---

# 53. MCP

For a larger agentic architecture, I would consider MCP.

Potential MCP tools:

```text
Booking Tool
Flight Search Tool
Refund Tool
Customer Tool
Notification Tool
```

The goal is to expose business capabilities in a standardized tool interface.

---

# 54. DATABASE — POSTGRESQL

SQLite is useful for development.

For production I would move to PostgreSQL.

Potential tables:

```text
users
conversations
messages
sessions
agent_state
audit_logs
feedback
```

PostgreSQL would be better suited to a production multi-user application.

---

# 55. DOCKER

I would containerize the application.

Potential architecture:

```text
Docker
 │
 ├── FastAPI
 ├── React
 └── Supporting services
```

Managed services:

```text
Neo4j Aura
PostgreSQL
LLM Provider
```

Docker would make the environment more reproducible.

---

# 56. SECURITY

For production I would add:

```text
Authentication
Authorization
Input validation
Rate limiting
Secret management
PII protection
Role-based access
Audit logs
```

API keys should remain outside source code.

---

# 57. OBSERVABILITY

I would monitor:

```text
Request latency
Retrieval latency
Reranker latency
LLM latency
Token usage
LLM cost
Cache hit rate
Fallback rate
Error rate
Retrieval scores
Tool failures
User feedback
```

Example:

```text
Retrieval      → 180 ms
Reranker       → 90 ms
LLM            → 850 ms
Total          → 1.12 sec
```

This helps identify performance bottlenecks.

---

# 58. FINAL PRODUCTION ARCHITECTURE

My target architecture is:

```text
                         USER
                           │
                           ▼
                       React UI
                           │
                           ▼
                        FastAPI
                           │
                           ▼
                    Authentication
                           │
                           ▼
                    Semantic Cache
                           │
                    Cache Hit?
                    ┌──────┴──────┐
                    │             │
                   YES            NO
                    │             │
                    ▼             ▼
                 Answer       LangGraph
                                  │
                                  ▼
                            Query Router
                                  │
                ┌─────────────────┼─────────────────┐
                │                 │                 │
                ▼                 ▼                 ▼
             RAG Agent       Graph Agent       Tool Agent
                │                 │                 │
         Chroma + BM25         Neo4j          Business APIs
                │                 │                 │
                └─────────────────┼─────────────────┘
                                  ▼
                              Reranker
                                  │
                                  ▼
                         Context Validation
                                  │
                                  ▼
                                 LLM
                                  │
                         ┌────────┴────────┐
                         │                 │
                    Normal Answer      Action Required
                         │                 │
                         │            Human Approval
                         │                 │
                         └────────┬────────┘
                                  ▼
                               Response
                                  │
                                  ▼
                             Save / Cache
                                  │
                                  ▼
                                 USER
```

---

# 59. THE SIMPLE STORY OF MY PROJECT

If I forget everything during an interview, I only need to remember:

```text
User
 ↓
Cache
 ↓
LangGraph
 ↓
Vector + BM25
 ↓
RRF
 ↓
Reranker
 ↓
Neo4j
 ↓
Combined Context
 ↓
LLM
 ↓
Answer
```

And six WHY answers:

```text
Chroma
→ Semantic search

BM25
→ Exact keyword matching

RRF
→ Combine retrieval rankings

Reranker
→ Improve final document ranking

Neo4j
→ Relationship-based retrieval

LangGraph
→ Control workflow and state
```

---

# 60. Explain your HolidayBreakz project


I would say:

> "HolidayBreakz is an AI customer-support assistant that I built to answer customer questions from a company knowledge base while reducing hallucinations.
>
> The backend uses FastAPI and LangGraph. For retrieval, I started with Chroma vector search, but I found that semantic search alone wasn't reliable for every question, especially exact product terms such as Refund Shield and Cancellation Protection.
>
> So I added BM25 for keyword matching and combined vector and BM25 rankings using Reciprocal Rank Fusion. After that, I added a CrossEncoder reranker to improve the final ordering of retrieved documents.
>
> I also introduced Neo4j because some information is relationship-based. For example, Seat can have relationships to Window Seat, Aisle Seat, Middle Seat and Extra Legroom.
>
> The RAG and graph results are combined and passed to the LLM through LangGraph.
>
> I also implemented semantic caching, SQLite checkpointing, fallback handling and retry logic.
>
> For evaluation, I created datasets using Recall@4, Precision@4, Hit Rate@4 and MRR. I also created a separate near-miss dataset to test similar questions that require different chunks.
>
> One important failure was that my initial evaluation dataset had incorrect ground-truth chunk IDs. I corrected the dataset after inspecting the knowledge-base chunks. Another challenge was that vector retrieval alone wasn't enough, which led me to BM25, RRF and reranking.
>
> The next step is query routing so the system can decide whether a question needs RAG, Graph RAG, or both. After that I want to add tools, human-in-the-loop, PostgreSQL, Docker and production monitoring."

---

# 61. WHAT THIS PROJECT TAUGHT ME

The biggest lesson was:

> **Building an Agentic AI system is not just about calling an LLM.**

It involves:

```text
Data
 ↓
Retrieval
 ↓
Ranking
 ↓
Knowledge Graph
 ↓
Workflow
 ↓
Caching
 ↓
Evaluation
 ↓
Error Handling
 ↓
Production Engineering
```

And my biggest mindset change was:

```text
Don't just build.

Measure.

Don't just retrieve.

Evaluate.

Don't just ask the LLM.

Ground it.

Don't just make a demo.

Design for production.
```

This project is helping me move from **AI automation and low-code workflows toward deeper Agentic AI engineering with Python, RAG, LangGraph, Neo4j and production-oriented architecture.**
