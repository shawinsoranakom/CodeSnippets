async def _aget_relevant_documents(
        self,
        query: str,
        *,
        run_manager: AsyncCallbackManagerForRetrieverRun,
    ) -> list[Document]:
        """Asynchronously get documents relevant to a query.

        Args:
            query: String to find relevant documents for
            run_manager: The callbacks handler to use
        Returns:
            List of relevant documents.
        """
        if self.search_type == SearchType.mmr:
            sub_docs = await self.vectorstore.amax_marginal_relevance_search(
                query,
                **self.search_kwargs,
            )
        elif self.search_type == SearchType.similarity_score_threshold:
            sub_docs_and_similarities = (
                await self.vectorstore.asimilarity_search_with_relevance_scores(
                    query,
                    **self.search_kwargs,
                )
            )
            sub_docs = [sub_doc for sub_doc, _ in sub_docs_and_similarities]
        else:
            sub_docs = await self.vectorstore.asimilarity_search(
                query,
                **self.search_kwargs,
            )

        # We do this to maintain the order of the IDs that are returned
        ids = []
        for d in sub_docs:
            if self.id_key in d.metadata and d.metadata[self.id_key] not in ids:
                ids.append(d.metadata[self.id_key])
        docs = await self.docstore.amget(ids)
        return [d for d in docs if d is not None]