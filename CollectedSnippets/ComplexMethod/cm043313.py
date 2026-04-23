def _calculate_bm25_score(self, query: str, documents: List[str]) -> List[float]:
        """Calculate BM25 scores for documents against a query."""
        if not HAS_BM25:
            self._log(
                "warning", "rank_bm25 not installed. Returning zero scores.", tag="URL_SEED")
            return [0.0] * len(documents)

        if not query or not documents:
            return [0.0] * len(documents)

        # Tokenize query and documents (simple whitespace tokenization)
        # For production, consider using a proper tokenizer
        query_tokens = query.lower().split()
        tokenized_docs = [doc.lower().split() for doc in documents]

        # Handle edge case where all documents are empty
        if all(len(doc) == 0 for doc in tokenized_docs):
            return [0.0] * len(documents)

        # Create BM25 instance and calculate scores
        try:
            from rank_bm25 import BM25Okapi
            bm25 = BM25Okapi(tokenized_docs)
            scores = bm25.get_scores(query_tokens)

            # Normalize scores to 0-1 range
            # BM25 can return negative scores, so we need to handle the full range
            if len(scores) == 0:
                return []

            min_score = min(scores)
            max_score = max(scores)

            # If all scores are the same, return 0.5 for all
            if max_score == min_score:
                return [0.5] * len(scores)

            # Normalize to 0-1 range using min-max normalization
            normalized_scores = [(score - min_score) / (max_score - min_score) for score in scores]

            return normalized_scores
        except Exception as e:
            self._log("error", "Error calculating BM25 scores: {error}",
                      params={"error": str(e)}, tag="URL_SEED")
            return [0.0] * len(documents)