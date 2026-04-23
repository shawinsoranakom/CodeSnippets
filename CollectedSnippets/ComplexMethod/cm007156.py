def _add_documents_to_vector_store(self, client: OpenSearch) -> None:
        """Process and ingest documents into the OpenSearch vector store.

        This method handles the complete document ingestion pipeline:
        - Prepares document data and metadata
        - Generates vector embeddings
        - Creates appropriate index mappings
        - Bulk inserts documents with vectors

        Args:
            client: OpenSearch client for performing operations
        """
        # Convert DataFrame to Data if needed using parent's method
        self.ingest_data = self._prepare_ingest_data()

        docs = self.ingest_data or []
        if not docs:
            self.log("No documents to ingest.")
            return

        # Extract texts and metadata from documents
        texts = []
        metadatas = []
        # Process docs_metadata table input into a dict
        additional_metadata = {}
        if hasattr(self, "docs_metadata") and self.docs_metadata:
            logger.debug(f"[LF] Docs metadata {self.docs_metadata}")
            if isinstance(self.docs_metadata[-1], Data):
                logger.debug(f"[LF] Docs metadata is a Data object {self.docs_metadata}")
                self.docs_metadata = self.docs_metadata[-1].data
                logger.debug(f"[LF] Docs metadata is a Data object {self.docs_metadata}")
                additional_metadata.update(self.docs_metadata)
            else:
                for item in self.docs_metadata:
                    if isinstance(item, dict) and "key" in item and "value" in item:
                        additional_metadata[item["key"]] = item["value"]
        # Replace string "None" values with actual None
        for key, value in additional_metadata.items():
            if value == "None":
                additional_metadata[key] = None
        logger.debug(f"[LF] Additional metadata {additional_metadata}")
        for doc_obj in docs:
            data_copy = json.loads(doc_obj.model_dump_json())
            text = data_copy.pop(doc_obj.text_key, doc_obj.default_value)
            texts.append(text)

            # Merge additional metadata from table input
            data_copy.update(additional_metadata)

            metadatas.append(data_copy)
        self.log(metadatas)
        if not self.embedding:
            msg = "Embedding handle is required to embed documents."
            raise ValueError(msg)

        # Generate embeddings
        vectors = self.embedding.embed_documents(texts)

        if not vectors:
            self.log("No vectors generated from documents.")
            return

        # Get vector dimension for mapping
        dim = len(vectors[0]) if vectors else 768  # default fallback

        # Check for AOSS
        auth_kwargs = self._build_auth_kwargs()
        is_aoss = self._is_aoss_enabled(auth_kwargs.get("http_auth"))

        # Validate engine with AOSS
        engine = getattr(self, "engine", "jvector")
        self._validate_aoss_with_engines(is_aoss=is_aoss, engine=engine)

        # Create mapping with proper KNN settings
        space_type = getattr(self, "space_type", "l2")
        ef_construction = getattr(self, "ef_construction", 512)
        m = getattr(self, "m", 16)

        mapping = self._default_text_mapping(
            dim=dim,
            engine=engine,
            space_type=space_type,
            ef_construction=ef_construction,
            m=m,
            vector_field=self.vector_field,
        )

        # Ensure index exists with proper KNN mapping (index.knn: true is required for vector search)
        try:
            if not client.indices.exists(index=self.index_name):
                self.log(f"Creating index '{self.index_name}' with KNN mapping (index.knn: true)")
                client.indices.create(index=self.index_name, body=mapping)
        except RequestError as creation_error:
            error_msg = str(creation_error).lower()
            if "invalid engine" in error_msg or "illegal_argument" in error_msg:
                if "jvector" in error_msg:
                    msg = (
                        "The 'jvector' engine is not available in your OpenSearch installation. "
                        "Use 'nmslib' or 'faiss' for standard OpenSearch, or upgrade to OpenSearch 2.9+."
                    )
                    raise ValueError(msg) from creation_error
                if "index.knn" in error_msg:
                    msg = (
                        "The index has index.knn: false. Delete the existing index and let the "
                        "component recreate it, or create a new index with a different name."
                    )
                    raise ValueError(msg) from creation_error
            raise

        self.log(f"Indexing {len(texts)} documents into '{self.index_name}' with proper KNN mapping...")

        # Use the LangChain-style bulk ingestion
        return_ids = self._bulk_ingest_embeddings(
            client=client,
            index_name=self.index_name,
            embeddings=vectors,
            texts=texts,
            metadatas=metadatas,
            vector_field=self.vector_field,
            text_field="text",
            mapping=mapping,
            is_aoss=is_aoss,
        )
        self.log(metadatas)

        self.log(f"Successfully indexed {len(return_ids)} documents.")