def build_vector_store(self):
        try:
            from langchain_astradb import AstraDBGraphVectorStore
            from langchain_astradb.utils.astradb import SetupMode
        except ImportError as e:
            msg = (
                "Could not import langchain Astra DB integration package. "
                "Please install it with `pip install langchain-astradb`."
            )
            raise ImportError(msg) from e

        try:
            if not self.setup_mode:
                self.setup_mode = self._inputs["setup_mode"].options[0]

            setup_mode_value = SetupMode[self.setup_mode.upper()]
        except KeyError as e:
            msg = f"Invalid setup mode: {self.setup_mode}"
            raise ValueError(msg) from e

        try:
            self.log(f"Initializing Graph Vector Store {self.collection_name}")

            vector_store = AstraDBGraphVectorStore(
                embedding=self.embedding_model,
                collection_name=self.collection_name,
                metadata_incoming_links_key=self.metadata_incoming_links_key or "incoming_links",
                token=self.token,
                api_endpoint=self.get_api_endpoint(),
                namespace=self.get_keyspace(),
                environment=self.environment,
                metric=self.metric or None,
                batch_size=self.batch_size or None,
                bulk_insert_batch_concurrency=self.bulk_insert_batch_concurrency or None,
                bulk_insert_overwrite_concurrency=self.bulk_insert_overwrite_concurrency or None,
                bulk_delete_concurrency=self.bulk_delete_concurrency or None,
                setup_mode=setup_mode_value,
                pre_delete_collection=self.pre_delete_collection,
                metadata_indexing_include=[s for s in self.metadata_indexing_include if s] or None,
                metadata_indexing_exclude=[s for s in self.metadata_indexing_exclude if s] or None,
                collection_indexing_policy=orjson.loads(self.collection_indexing_policy.encode("utf-8"))
                if self.collection_indexing_policy
                else None,
            )
        except Exception as e:
            msg = f"Error initializing AstraDBGraphVectorStore: {e}"
            raise ValueError(msg) from e

        self.log(f"Vector Store initialized: {vector_store.astra_env.collection_name}")
        self._add_documents_to_vector_store(vector_store)

        return vector_store