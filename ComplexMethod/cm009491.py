def _similarity_search_with_score_by_vector(
        self,
        embedding: list[float],
        k: int = 4,
        filter: Callable[[Document], bool] | None = None,  # noqa: A002
    ) -> list[tuple[Document, float, list[float]]]:
        # Get all docs with fixed order in list
        docs = list(self.store.values())

        if filter is not None:
            docs = [
                doc
                for doc in docs
                if filter(
                    Document(
                        id=doc["id"], page_content=doc["text"], metadata=doc["metadata"]
                    )
                )
            ]

        if not docs:
            return []

        similarity = cosine_similarity([embedding], [doc["vector"] for doc in docs])[0]

        # Get the indices ordered by similarity score
        top_k_idx = similarity.argsort()[::-1][:k]

        return [
            (
                Document(
                    id=doc_dict["id"],
                    page_content=doc_dict["text"],
                    metadata=doc_dict["metadata"],
                ),
                float(similarity[idx].item()),
                doc_dict["vector"],
            )
            for idx in top_k_idx
            # Assign using walrus operator to avoid multiple lookups
            if (doc_dict := docs[idx])
        ]