def _build_vectors(
        self,
        texts: Iterable[str],
    ) -> list[models.VectorStruct]:
        if self.retrieval_mode == RetrievalMode.DENSE:
            embeddings = self._require_embeddings("DENSE mode")
            batch_embeddings = embeddings.embed_documents(list(texts))
            return [
                {
                    self.vector_name: vector,
                }
                for vector in batch_embeddings
            ]

        if self.retrieval_mode == RetrievalMode.SPARSE:
            batch_sparse_embeddings = self.sparse_embeddings.embed_documents(
                list(texts)
            )
            return [
                {
                    self.sparse_vector_name: models.SparseVector(
                        values=vector.values, indices=vector.indices
                    )
                }
                for vector in batch_sparse_embeddings
            ]

        if self.retrieval_mode == RetrievalMode.HYBRID:
            embeddings = self._require_embeddings("HYBRID mode")
            dense_embeddings = embeddings.embed_documents(list(texts))
            sparse_embeddings = self.sparse_embeddings.embed_documents(list(texts))

            if len(dense_embeddings) != len(sparse_embeddings):
                msg = "Mismatched length between dense and sparse embeddings."
                raise ValueError(msg)

            return [
                {
                    self.vector_name: dense_vector,
                    self.sparse_vector_name: models.SparseVector(
                        values=sparse_vector.values, indices=sparse_vector.indices
                    ),
                }
                for dense_vector, sparse_vector in zip(
                    dense_embeddings, sparse_embeddings, strict=False
                )
            ]

        msg = f"Unknown retrieval mode. {self.retrieval_mode} to build vectors."
        raise ValueError(msg)