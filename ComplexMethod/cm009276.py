def construct_instance(
        cls: type[QdrantVectorStore],
        embedding: Embeddings | None = None,
        retrieval_mode: RetrievalMode = RetrievalMode.DENSE,
        sparse_embedding: SparseEmbeddings | None = None,
        client_options: dict[str, Any] | None = None,
        collection_name: str | None = None,
        distance: models.Distance = models.Distance.COSINE,
        content_payload_key: str = CONTENT_KEY,
        metadata_payload_key: str = METADATA_KEY,
        vector_name: str = VECTOR_NAME,
        sparse_vector_name: str = SPARSE_VECTOR_NAME,
        force_recreate: bool = False,  # noqa: FBT001, FBT002
        collection_create_options: dict[str, Any] | None = None,
        vector_params: dict[str, Any] | None = None,
        sparse_vector_params: dict[str, Any] | None = None,
        validate_embeddings: bool = True,  # noqa: FBT001, FBT002
        validate_collection_config: bool = True,  # noqa: FBT001, FBT002
    ) -> QdrantVectorStore:
        if sparse_vector_params is None:
            sparse_vector_params = {}
        if vector_params is None:
            vector_params = {}
        if collection_create_options is None:
            collection_create_options = {}
        if client_options is None:
            client_options = {}
        if validate_embeddings:
            cls._validate_embeddings(retrieval_mode, embedding, sparse_embedding)
        collection_name = collection_name or uuid.uuid4().hex
        client = QdrantClient(**client_options)

        collection_exists = client.collection_exists(collection_name)

        if collection_exists and force_recreate:
            client.delete_collection(collection_name)
            collection_exists = False
        if collection_exists:
            if validate_collection_config:
                cls._validate_collection_config(
                    client,
                    collection_name,
                    retrieval_mode,
                    vector_name,
                    sparse_vector_name,
                    distance,
                    embedding,
                )
        else:
            vectors_config, sparse_vectors_config = {}, {}
            if retrieval_mode == RetrievalMode.DENSE:
                partial_embeddings = embedding.embed_documents(["dummy_text"])  # type: ignore[union-attr]

                vector_params["size"] = len(partial_embeddings[0])
                vector_params["distance"] = distance

                vectors_config = {
                    vector_name: models.VectorParams(
                        **vector_params,
                    )
                }

            elif retrieval_mode == RetrievalMode.SPARSE:
                sparse_vectors_config = {
                    sparse_vector_name: models.SparseVectorParams(
                        **sparse_vector_params
                    )
                }

            elif retrieval_mode == RetrievalMode.HYBRID:
                partial_embeddings = embedding.embed_documents(["dummy_text"])  # type: ignore[union-attr]

                vector_params["size"] = len(partial_embeddings[0])
                vector_params["distance"] = distance

                vectors_config = {
                    vector_name: models.VectorParams(
                        **vector_params,
                    )
                }

                sparse_vectors_config = {
                    sparse_vector_name: models.SparseVectorParams(
                        **sparse_vector_params
                    )
                }

            collection_create_options["collection_name"] = collection_name
            collection_create_options["vectors_config"] = vectors_config
            collection_create_options["sparse_vectors_config"] = sparse_vectors_config

            client.create_collection(**collection_create_options)

        return cls(
            client=client,
            collection_name=collection_name,
            embedding=embedding,
            retrieval_mode=retrieval_mode,
            content_payload_key=content_payload_key,
            metadata_payload_key=metadata_payload_key,
            distance=distance,
            vector_name=vector_name,
            sparse_embedding=sparse_embedding,
            sparse_vector_name=sparse_vector_name,
            validate_embeddings=False,
            validate_collection_config=False,
        )