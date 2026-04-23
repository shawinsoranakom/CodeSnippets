def __init__(
        self,
        client: Any,
        collection_name: str,
        embeddings: Embeddings | None = None,
        content_payload_key: str = CONTENT_KEY,
        metadata_payload_key: str = METADATA_KEY,
        distance_strategy: str = "COSINE",
        vector_name: str | None = VECTOR_NAME,
        async_client: Any | None = None,
        embedding_function: Callable | None = None,  # deprecated
    ) -> None:
        """Initialize with necessary components."""
        if not isinstance(client, QdrantClient):
            msg = (
                f"client should be an instance of qdrant_client.QdrantClient, "
                f"got {type(client)}"
            )
            raise TypeError(msg)

        if async_client is not None and not isinstance(async_client, AsyncQdrantClient):
            msg = (
                f"async_client should be an instance of qdrant_client.AsyncQdrantClient"
                f"got {type(async_client)}"
            )
            raise ValueError(msg)

        if embeddings is None and embedding_function is None:
            msg = "`embeddings` value can't be None. Pass `embeddings` instance."
            raise ValueError(msg)

        if embeddings is not None and embedding_function is not None:
            msg = (
                "Both `embeddings` and `embedding_function` are passed. "
                "Use `embeddings` only."
            )
            raise ValueError(msg)

        self._embeddings = embeddings
        self._embeddings_function = embedding_function
        self.client: QdrantClient = client
        self.async_client: AsyncQdrantClient | None = async_client
        self.collection_name = collection_name
        self.content_payload_key = content_payload_key or self.CONTENT_KEY
        self.metadata_payload_key = metadata_payload_key or self.METADATA_KEY
        self.vector_name = vector_name or self.VECTOR_NAME

        if embedding_function is not None:
            warnings.warn(
                "Using `embedding_function` is deprecated. "
                "Pass `Embeddings` instance to `embeddings` instead.",
                stacklevel=2,
            )

        if not isinstance(embeddings, Embeddings):
            warnings.warn(
                "`embeddings` should be an instance of `Embeddings`."
                "Using `embeddings` as `embedding_function` which is deprecated",
                stacklevel=2,
            )
            self._embeddings_function = embeddings
            self._embeddings = None

        self.distance_strategy = distance_strategy.upper()