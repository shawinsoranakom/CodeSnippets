def __init__(
        self,
        collection_name: str = _LANGCHAIN_DEFAULT_COLLECTION_NAME,
        embedding_function: Embeddings | None = None,
        persist_directory: str | None = None,
        host: str | None = None,
        port: int | None = None,
        headers: dict[str, str] | None = None,
        chroma_cloud_api_key: str | None = None,
        tenant: str | None = None,
        database: str | None = None,
        client_settings: chromadb.config.Settings | None = None,
        collection_metadata: dict | None = None,
        collection_configuration: CreateCollectionConfiguration | None = None,
        client: chromadb.ClientAPI | None = None,
        relevance_score_fn: Callable[[float], float] | None = None,
        create_collection_if_not_exists: bool | None = True,  # noqa: FBT001, FBT002
        *,
        ssl: bool = False,
    ) -> None:
        """Initialize with a Chroma client.

        Args:
            collection_name: Name of the collection to create.
            embedding_function: Embedding class object. Used to embed texts.
            persist_directory: Directory to persist the collection.
            host: Hostname of a deployed Chroma server.
            port: Connection port for a deployed Chroma server. Default is 8000.
            ssl: Whether to establish an SSL connection with a deployed Chroma server.
                    Default is False.
            headers: HTTP headers to send to a deployed Chroma server.
            chroma_cloud_api_key: Chroma Cloud API key.
            tenant: Tenant ID. Required for Chroma Cloud connections.
                    Default is 'default_tenant' for local Chroma servers.
            database: Database name. Required for Chroma Cloud connections.
                    Default is 'default_database'.
            client_settings: Chroma client settings
            collection_metadata: Collection configurations.
            collection_configuration: Index configuration for the collection.

            client: Chroma client. Documentation:
                    https://docs.trychroma.com/reference/python/client
            relevance_score_fn: Function to calculate relevance score from distance.
                    Used only in `similarity_search_with_relevance_scores`
            create_collection_if_not_exists: Whether to create collection
                    if it doesn't exist. Defaults to `True`.
        """
        _tenant = tenant or chromadb.DEFAULT_TENANT
        _database = database or chromadb.DEFAULT_DATABASE
        _settings = client_settings or Settings()

        client_args = {
            "persist_directory": persist_directory,
            "host": host,
            "chroma_cloud_api_key": chroma_cloud_api_key,
        }

        if sum(arg is not None for arg in client_args.values()) > 1:
            provided = [
                name for name, value in client_args.items() if value is not None
            ]
            msg = (
                f"Only one of 'persist_directory', 'host' and 'chroma_cloud_api_key' "
                f"is allowed, but got {','.join(provided)}"
            )
            raise ValueError(msg)

        if client is not None:
            self._client = client

        # PersistentClient
        elif persist_directory is not None:
            self._client = chromadb.PersistentClient(
                path=persist_directory,
                settings=_settings,
                tenant=_tenant,
                database=_database,
            )

        # HttpClient
        elif host is not None:
            _port = port or 8000
            self._client = chromadb.HttpClient(
                host=host,
                port=_port,
                ssl=ssl,
                headers=headers,
                settings=_settings,
                tenant=_tenant,
                database=_database,
            )

        # CloudClient
        elif chroma_cloud_api_key is not None:
            if not tenant or not database:
                msg = (
                    "Must provide tenant and database values to connect to Chroma Cloud"
                )
                raise ValueError(msg)
            self._client = chromadb.CloudClient(
                tenant=tenant,
                database=database,
                api_key=chroma_cloud_api_key,
                settings=_settings,
            )

        else:
            self._client = chromadb.Client(settings=_settings)

        self._embedding_function = embedding_function
        self._chroma_collection: chromadb.Collection | None = None
        self._collection_name = collection_name
        self._collection_metadata = collection_metadata
        self._collection_configuration = collection_configuration
        if create_collection_if_not_exists:
            self.__ensure_collection()
        else:
            self._chroma_collection = self._client.get_collection(name=collection_name)
        self.override_relevance_score_fn = relevance_score_fn