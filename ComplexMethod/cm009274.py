def from_texts(
        cls: type[Chroma],
        texts: list[str],
        embedding: Embeddings | None = None,
        metadatas: list[dict] | None = None,
        ids: list[str] | None = None,
        collection_name: str = _LANGCHAIN_DEFAULT_COLLECTION_NAME,
        persist_directory: str | None = None,
        host: str | None = None,
        port: int | None = None,
        headers: dict[str, str] | None = None,
        chroma_cloud_api_key: str | None = None,
        tenant: str | None = None,
        database: str | None = None,
        client_settings: chromadb.config.Settings | None = None,
        client: chromadb.ClientAPI | None = None,
        collection_metadata: dict | None = None,
        collection_configuration: CreateCollectionConfiguration | None = None,
        *,
        ssl: bool = False,
        **kwargs: Any,
    ) -> Chroma:
        """Create a Chroma vectorstore from a raw documents.

        If a persist_directory is specified, the collection will be persisted there.
        Otherwise, the data will be ephemeral in-memory.

        Args:
            texts: List of texts to add to the collection.
            collection_name: Name of the collection to create.
            persist_directory: Directory to persist the collection.
            host: Hostname of a deployed Chroma server.
            port: Connection port for a deployed Chroma server.
                    Default is 8000.
            ssl: Whether to establish an SSL connection with a deployed Chroma server.
                    Default is False.
            headers: HTTP headers to send to a deployed Chroma server.
            chroma_cloud_api_key: Chroma Cloud API key.
            tenant: Tenant ID. Required for Chroma Cloud connections.
                    Default is 'default_tenant' for local Chroma servers.
            database: Database name. Required for Chroma Cloud connections.
                    Default is 'default_database'.
            embedding: Embedding function.
            metadatas: List of metadatas.
            ids: List of document IDs.
            client_settings: Chroma client settings.
            client: Chroma client. Documentation:
                    https://docs.trychroma.com/reference/python/client
            collection_metadata: Collection configurations.
            collection_configuration: Index configuration for the collection.

            kwargs: Additional keyword arguments to initialize a Chroma client.

        Returns:
            Chroma: Chroma vectorstore.
        """
        chroma_collection = cls(
            collection_name=collection_name,
            embedding_function=embedding,
            persist_directory=persist_directory,
            host=host,
            port=port,
            ssl=ssl,
            headers=headers,
            chroma_cloud_api_key=chroma_cloud_api_key,
            tenant=tenant,
            database=database,
            client_settings=client_settings,
            client=client,
            collection_metadata=collection_metadata,
            collection_configuration=collection_configuration,
            **kwargs,
        )
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in texts]
        else:
            ids = [id_ if id_ is not None else str(uuid.uuid4()) for id_ in ids]
        if hasattr(
            chroma_collection._client,
            "get_max_batch_size",
        ) or hasattr(  # for Chroma 0.5.1 and above
            chroma_collection._client,
            "max_batch_size",
        ):  # for Chroma 0.4.10 and above
            from chromadb.utils.batch_utils import create_batches

            for batch in create_batches(
                api=chroma_collection._client,
                ids=ids,
                metadatas=metadatas,  # type: ignore[arg-type]
                documents=texts,
            ):
                chroma_collection.add_texts(
                    texts=batch[3] if batch[3] else [],
                    metadatas=batch[2] if batch[2] else None,  # type: ignore[arg-type]
                    ids=batch[0],
                )
        else:
            chroma_collection.add_texts(texts=texts, metadatas=metadatas, ids=ids)
        return chroma_collection