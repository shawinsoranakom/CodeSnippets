def _validate_collection_for_dense(
        cls: type[QdrantVectorStore],
        client: QdrantClient,
        collection_name: str,
        vector_name: str,
        distance: models.Distance,
        dense_embeddings: Embeddings | list[float] | None,
    ) -> None:
        collection_info = client.get_collection(collection_name=collection_name)
        vector_config = collection_info.config.params.vectors

        if isinstance(vector_config, dict):
            # vector_config is a Dict[str, VectorParams]
            if vector_name not in vector_config:
                msg = (
                    f"Existing Qdrant collection {collection_name} does not "
                    f"contain dense vector named {vector_name}. "
                    "Did you mean one of the "
                    f"existing vectors: {', '.join(vector_config.keys())}? "  # type: ignore[union-attr]
                    f"If you want to recreate the collection, set `force_recreate` "
                    f"parameter to `True`."
                )
                raise QdrantVectorStoreError(msg)

            # Get the VectorParams object for the specified vector_name
            vector_config = vector_config[vector_name]  # type: ignore[assignment, index]

        # vector_config is an instance of VectorParams
        # Case of a collection with single/unnamed vector.
        elif vector_name != "":
            msg = (
                f"Existing Qdrant collection {collection_name} is built "
                "with unnamed dense vector. "
                f"If you want to reuse it, set `vector_name` to ''(empty string)."
                f"If you want to recreate the collection, "
                "set `force_recreate` to `True`."
            )
            raise QdrantVectorStoreError(msg)

        if vector_config is None:
            msg = "VectorParams is None"
            raise ValueError(msg)

        if isinstance(dense_embeddings, Embeddings):
            vector_size = len(dense_embeddings.embed_documents(["dummy_text"])[0])
        elif isinstance(dense_embeddings, list):
            vector_size = len(dense_embeddings)
        else:
            msg = "Invalid `embeddings` type."
            raise TypeError(msg)

        if vector_config.size != vector_size:
            msg = (
                f"Existing Qdrant collection is configured for dense vectors with "
                f"{vector_config.size} dimensions. "
                f"Selected embeddings are {vector_size}-dimensional. "
                f"If you want to recreate the collection, set `force_recreate` "
                f"parameter to `True`."
            )
            raise QdrantVectorStoreError(msg)

        if vector_config.distance != distance:
            msg = (
                f"Existing Qdrant collection is configured for "
                f"{vector_config.distance.name} similarity, but requested "
                f"{distance.upper()}. Please set `distance` parameter to "
                f"`{vector_config.distance.name}` if you want to reuse it. "
                f"If you want to recreate the collection, set `force_recreate` "
                f"parameter to `True`."
            )
            raise QdrantVectorStoreError(msg)