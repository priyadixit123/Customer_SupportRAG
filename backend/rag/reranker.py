from sentence_transformers import CrossEncoder


class Reranker:

    def __init__(self):

        self.model = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L-6-v2"
        )


    def rerank(
        self,
        query,
        documents,
        k=4
    ):

        if not documents:

            return []


        # Create query-document pairs
        pairs = []

        for document in documents:

            pairs.append(
                (
                    query,
                    document.page_content
                )
            )


        # CrossEncoder scores each pair
        scores = self.model.predict(pairs)


        results = []


        for document, score in zip(
            documents,
            scores
        ):

            results.append(
                {
                    "document": document,
                    "score": float(score)
                }
            )


        # Highest score first
        results.sort(
            key=lambda x: x["score"],
            reverse=True
        )


        # Return top K
        return results[:k]