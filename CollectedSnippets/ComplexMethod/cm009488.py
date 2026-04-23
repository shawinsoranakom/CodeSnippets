async def asimilarity_search_with_relevance_scores(
        self,
        query: str,
        k: int = 4,
        **kwargs: Any,
    ) -> list[tuple[Document, float]]:
        """Async return docs and relevance scores in the range `[0, 1]`.

        `0` is dissimilar, `1` is most similar.

        Args:
            query: Input text.
            k: Number of `Document` objects to return.
            **kwargs: Kwargs to be passed to similarity search.

                Should include `score_threshold`, an optional floating point value
                between `0` to `1` to filter the resulting set of retrieved docs.

        Returns:
            List of tuples of `(doc, similarity_score)`
        """
        score_threshold = kwargs.pop("score_threshold", None)

        docs_and_similarities = await self._asimilarity_search_with_relevance_scores(
            query, k=k, **kwargs
        )
        if any(
            similarity < 0.0 or similarity > 1.0
            for _, similarity in docs_and_similarities
        ):
            warnings.warn(
                "Relevance scores must be between"
                f" 0 and 1, got {docs_and_similarities}",
                stacklevel=2,
            )

        if score_threshold is not None:
            docs_and_similarities = [
                (doc, similarity)
                for doc, similarity in docs_and_similarities
                if similarity >= score_threshold
            ]
            if len(docs_and_similarities) == 0:
                logger.warning(
                    "No relevant docs were retrieved using the "
                    "relevance score threshold %s",
                    score_threshold,
                )
        return docs_and_similarities