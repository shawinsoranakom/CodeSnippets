def search(self, query: str | None = None) -> list[dict[str, Any]]:
        """Search for similar documents in the vector store or retrieve all documents if no query is provided."""
        vector_store = self.build_vector_store()
        search_kwargs = {
            "k": self.number_of_results,
            "score_threshold": self.search_score_threshold,
        }

        if query:
            search_type = self.search_type.lower()
            if search_type not in {"similarity", "mmr"}:
                msg = f"Invalid search type: {self.search_type}"
                self.log(msg)
                raise ValueError(msg)
            try:
                if search_type == "similarity":
                    results = vector_store.similarity_search_with_score(query, **search_kwargs)
                elif search_type == "mmr":
                    results = vector_store.max_marginal_relevance_search(query, **search_kwargs)
            except Exception as e:
                msg = (
                    "Error occurred while querying the Elasticsearch VectorStore,"
                    " there is no Data into the VectorStore."
                )
                self.log(msg)
                raise ValueError(msg) from e
            return [
                {"page_content": doc.page_content, "metadata": doc.metadata, "score": score} for doc, score in results
            ]
        results = self.get_all_documents(vector_store, **search_kwargs)
        return [{"page_content": doc.page_content, "metadata": doc.metadata, "score": score} for doc, score in results]