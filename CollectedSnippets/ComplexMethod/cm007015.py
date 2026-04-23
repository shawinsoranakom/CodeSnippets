def build_vector_store(self):
        try:
            from langchain_astradb import AstraDBVectorStore
            from langchain_astradb.utils.astradb import HybridSearchMode
        except ImportError as e:
            msg = (
                "Could not import langchain Astra DB integration package. "
                "Please install it with `pip install langchain-astradb`."
            )
            raise ImportError(msg) from e

        # Resolve the embedding model from ModelInput selection to an Embeddings instance
        embedding = None
        if self.embedding_model:
            embedding = get_embeddings(
                model=self.embedding_model,
                user_id=self.user_id,
                api_key=getattr(self, "api_key", None),
            )
        embedding_params = {"embedding": embedding} if embedding else {}

        # Get the additional parameters
        additional_params = self.astradb_vectorstore_kwargs or {}

        # Get Langflow version and platform information
        __version__ = get_version_info()["version"]
        langflow_prefix = ""
        # if os.getenv("AWS_EXECUTION_ENV") == "AWS_ECS_FARGATE":  # TODO: More precise way of detecting
        #     langflow_prefix = "ds-"

        # Get the database object
        database = self.get_database_object()
        autodetect = self.collection_name in database.list_collection_names() and self.autodetect_collection

        # Bundle up the auto-detect parameters
        autodetect_params = {
            "autodetect_collection": autodetect,
            "content_field": (
                self.content_field
                if self.content_field and embedding_params
                else (
                    "page_content"
                    if embedding_params
                    and self.collection_data(collection_name=self.collection_name, database=database) == 0
                    else None
                )
            ),
            "ignore_invalid_documents": self.ignore_invalid_documents,
        }

        # Choose HybridSearchMode based on the selected param
        hybrid_search_mode = HybridSearchMode.DEFAULT if self.search_method == "Hybrid Search" else HybridSearchMode.OFF

        # Attempt to build the Vector Store object
        try:
            vector_store = AstraDBVectorStore(
                # Astra DB Authentication Parameters
                token=self.token,
                api_endpoint=database.api_endpoint,
                namespace=database.keyspace,
                collection_name=self.collection_name,
                environment=self.environment,
                # Hybrid Search Parameters
                hybrid_search=hybrid_search_mode,
                # Astra DB Usage Tracking Parameters
                ext_callers=[(f"{langflow_prefix}langflow", __version__)],
                # Astra DB Vector Store Parameters
                **autodetect_params,
                **embedding_params,
                **additional_params,
            )
        except ValueError as e:
            msg = f"Error initializing AstraDBVectorStore: {e}"
            raise ValueError(msg) from e

        # Add documents to the vector store
        self._add_documents_to_vector_store(vector_store)

        return vector_store