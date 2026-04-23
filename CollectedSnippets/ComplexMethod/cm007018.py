def build_vector_store(self):
        try:
            from langchain_astradb import AstraDBVectorStore
            from langchain_astradb.utils.astradb import SetupMode
        except ImportError as e:
            msg = (
                "Could not import langchain Astra DB integration package. "
                "Please install it with `pip install langchain-astradb`."
            )
            raise ImportError(msg) from e

        try:
            from astrapy.authentication import UsernamePasswordTokenProvider
            from astrapy.constants import Environment
        except ImportError as e:
            msg = "Could not import astrapy integration package. Please install it with `pip install astrapy`."
            raise ImportError(msg) from e

        try:
            if not self.setup_mode:
                self.setup_mode = self._inputs["setup_mode"].options[0]

            setup_mode_value = SetupMode[self.setup_mode.upper()]
        except KeyError as e:
            msg = f"Invalid setup mode: {self.setup_mode}"
            raise ValueError(msg) from e

        if not isinstance(self.embedding, dict):
            embedding_dict = {"embedding": self.embedding}
        else:
            from astrapy.info import VectorServiceOptions

            dict_options = self.embedding.get("collection_vector_service_options", {})
            dict_options["authentication"] = {
                k: v for k, v in dict_options.get("authentication", {}).items() if k and v
            }
            dict_options["parameters"] = {k: v for k, v in dict_options.get("parameters", {}).items() if k and v}
            embedding_dict = {"collection_vector_service_options": VectorServiceOptions.from_dict(dict_options)}
            collection_embedding_api_key = self.embedding.get("collection_embedding_api_key")
            if collection_embedding_api_key:
                embedding_dict["collection_embedding_api_key"] = collection_embedding_api_key

        token_provider = UsernamePasswordTokenProvider(self.username, self.password)
        vector_store_kwargs = {
            **embedding_dict,
            "collection_name": self.collection_name,
            "token": token_provider,
            "api_endpoint": self.api_endpoint,
            "namespace": self.namespace,
            "metric": self.metric or None,
            "batch_size": self.batch_size or None,
            "bulk_insert_batch_concurrency": self.bulk_insert_batch_concurrency or None,
            "bulk_insert_overwrite_concurrency": self.bulk_insert_overwrite_concurrency or None,
            "bulk_delete_concurrency": self.bulk_delete_concurrency or None,
            "setup_mode": setup_mode_value,
            "pre_delete_collection": self.pre_delete_collection or False,
            "environment": Environment.HCD,
        }

        if self.metadata_indexing_include:
            vector_store_kwargs["metadata_indexing_include"] = self.metadata_indexing_include
        elif self.metadata_indexing_exclude:
            vector_store_kwargs["metadata_indexing_exclude"] = self.metadata_indexing_exclude
        elif self.collection_indexing_policy:
            vector_store_kwargs["collection_indexing_policy"] = self.collection_indexing_policy

        try:
            vector_store = AstraDBVectorStore(**vector_store_kwargs)
        except Exception as e:
            msg = f"Error initializing AstraDBVectorStore: {e}"
            raise ValueError(msg) from e

        self._add_documents_to_vector_store(vector_store)
        return vector_store