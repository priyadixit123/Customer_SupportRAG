from sentence_transformers import CrossEncoder
from sentence_transformers import CrossEncoder



class Reranker:
    def __init__(self):
        self.model = None

    def _load_model(self):
        if self.model is None:
            from sentence_transformers import CrossEncoder

            self.model = CrossEncoder(
                "cross-encoder/ms-marco-MiniLM-L-6-v2"
            )

    def rerank(self, query, documents, k=4):
        if not documents:
            return []

        self._load_model()

        pairs = [
            (query, document.page_content)
            for document in documents
        ]

        scores = self.model.predict(pairs)

        results = [
            {
                "document": document,
                "score": float(score),
            }
            for document, score in zip(documents, scores)
        ]

        results.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        return results[:k]


            