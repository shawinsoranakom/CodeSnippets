def filter_documents_embeddings(
        self, documents: List[str], semantic_filter: str, at_least_k: int = 20
    ) -> List[str]:
        """
        Filter and sort documents based on the cosine similarity of their embeddings with the semantic_filter embedding.

        Args:
            documents (List[str]): A list of document texts.
            semantic_filter (str): A keyword filter for document filtering.
            at_least_k (int): The minimum number of documents to return.

        Returns:
            List[str]: A list of filtered and sorted document texts.
        """

        if not semantic_filter:
            return documents

        if len(documents) < at_least_k:
            at_least_k = max(1, len(documents) // 2)

        from sklearn.metrics.pairwise import cosine_similarity

        # Compute embedding for the keyword filter
        query_embedding = self.get_embeddings([semantic_filter])[0]

        # Compute embeddings for the documents
        document_embeddings = self.get_embeddings(documents)

        # Calculate cosine similarity between the query embedding and document embeddings
        similarities = cosine_similarity(
            [query_embedding], document_embeddings
        ).flatten()

        # Filter documents based on the similarity threshold
        filtered_docs = [
            (doc, sim)
            for doc, sim in zip(documents, similarities)
            if sim >= self.sim_threshold
        ]

        # If the number of filtered documents is less than at_least_k, sort remaining documents by similarity
        if len(filtered_docs) < at_least_k:
            remaining_docs = [
                (doc, sim)
                for doc, sim in zip(documents, similarities)
                if sim < self.sim_threshold
            ]
            remaining_docs.sort(key=lambda x: x[1], reverse=True)
            filtered_docs.extend(remaining_docs[: at_least_k - len(filtered_docs)])

        # Extract the document texts from the tuples
        filtered_docs = [doc for doc, _ in filtered_docs]

        return filtered_docs[:at_least_k]