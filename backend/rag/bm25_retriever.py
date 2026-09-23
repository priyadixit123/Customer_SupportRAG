from rank_bm25 import BM25Okapi


class BM25Retriever:

    def __init__(self, documents):
        self.documents = documents

        tokenized_docs = [
            doc.page_content.lower().split()
            for doc in documents
        ]

        self.bm25 = BM25Okapi(tokenized_docs)

    def search(self, query, k=4):

        tokenized_query = query.lower().split()

        scores = self.bm25.get_scores(tokenized_query)

        ranked_indexes = scores.argsort()[::-1][:k]

        results = []

        for index in ranked_indexes:
            results.append({
                "document": self.documents[index],
                "score": float(scores[index])
            })

        return results