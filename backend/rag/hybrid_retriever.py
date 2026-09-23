class HybridRetriever:

    def __init__(self, vector_retriever, bm25_retriever):

        self.vector_retriever = vector_retriever
        self.bm25_retriever = bm25_retriever

    def search(self, query, k=4):

        # Vector search
        vector_results = self.vector_retriever.invoke(query)

        # BM25 search
        bm25_results = self.bm25_retriever.search(
            query,
            k=k
        )

        # RRF
        scores = {}
        documents = {}

        rrf_k = 60

        # Vector ranking
        for rank, doc in enumerate(
            vector_results,
            start=1
        ):

            doc_id = doc.metadata.get(
                "chunk_id",
                doc.page_content
            )

            documents[doc_id] = doc

            scores[doc_id] = scores.get(
                doc_id,
                0
            ) + (1 / (rrf_k + rank))

        # BM25 ranking
        for rank, item in enumerate(
            bm25_results,
            start=1
        ):

            doc = item["document"]

            doc_id = doc.metadata.get(
                "chunk_id",
                doc.page_content
            )

            documents[doc_id] = doc

            scores[doc_id] = scores.get(
                doc_id,
                0
            ) + (1 / (rrf_k + rank))

        # Sort by RRF score
        ranked_documents = sorted(
            documents.items(),
            key=lambda x: scores[x[0]],
            reverse=True
        )

        # Return top K
        return [
            {
                "document": doc,
                "score": scores[doc_id]
            }
            for doc_id, doc in ranked_documents[:k]
        ]