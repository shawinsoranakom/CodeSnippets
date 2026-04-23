def rerank(
        self,
        documents: Sequence[str | Document | dict],
        query: str,
        *,
        model: str | None = None,
        top_n: int | None = -1,
        max_chunks_per_doc: int | None = None,
    ) -> list[dict[str, Any]]:
        """Returns an ordered list of documents ordered by their relevance to the provided query.

        Args:
            query: The query to use for reranking.
            documents: A sequence of documents to rerank.
            model: The model to use for re-ranking. Default to self.model.
            top_n : The number of results to return. If `None` returns all results.
            max_chunks_per_doc : The maximum number of chunks derived from a document.
        """  # noqa: E501
        if len(documents) == 0:  # to avoid empty api call
            return []
        docs = [
            doc.page_content if isinstance(doc, Document) else doc for doc in documents
        ]
        model = model or self.model
        top_n = top_n if (top_n is None or top_n > 0) else self.top_n
        results = self.client.rerank(
            query=query,
            documents=docs,
            model=model,
            top_n=top_n,
            max_chunks_per_doc=max_chunks_per_doc,
        )
        if hasattr(results, "results"):
            results = results.results
        return [
            {"index": res.index, "relevance_score": res.relevance_score}
            for res in results
        ]