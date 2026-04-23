def _add_documents_to_vector_store(self, client: OpenSearch) -> None:
        """Process and ingest documents into the OpenSearch vector store.

        This method handles the complete document ingestion pipeline:
        - Prepares document data and metadata
        - Generates vector embeddings using the selected model
        - Creates appropriate index mappings with dynamic field names
        - Bulk inserts documents with vectors and model tracking

        Args:
            client: OpenSearch client for performing operations
        """
        logger.debug("[OpenSearchMultimodel][INGESTION] _add_documents_to_vector_store called")
        # Convert DataFrame to Data if needed using parent's method
        self.ingest_data = self._prepare_ingest_data()

        logger.debug(
            f"[OpenSearchMultimodel][INGESTION] ingest_data type: "
            f"{type(self.ingest_data)}, length: {len(self.ingest_data) if self.ingest_data else 0}"
        )
        logger.debug(
            f"[OpenSearchMultimodel][INGESTION] ingest_data content: "
            f"{self.ingest_data[:2] if self.ingest_data and len(self.ingest_data) > 0 else 'empty'}"
        )

        docs = self.ingest_data or []
        if not docs:
            logger.debug("Ingestion complete: No documents provided")
            return

        if not self.embedding:
            msg = "Embedding handle is required to embed documents."
            raise ValueError(msg)

        # Normalize embedding to list first
        embeddings_list = self.embedding if isinstance(self.embedding, list) else [self.embedding]

        # Filter out None values (fail-safe mode) - do this BEFORE checking if empty
        embeddings_list = [e for e in embeddings_list if e is not None]

        # NOW check if we have any valid embeddings left after filtering
        if not embeddings_list:
            logger.warning("All embeddings returned None (fail-safe mode enabled). Skipping document ingestion.")
            self.log("Embedding returned None (fail-safe mode enabled). Skipping document ingestion.")
            return

        logger.debug(f"[OpenSearchMultimodel][INGESTION] Valid embeddings after filtering: {len(embeddings_list)}")
        self.log(f"[OpenSearchMultimodel][INGESTION] Available embedding models: {len(embeddings_list)}")

        # Select the embedding to use for ingestion
        selected_embedding = None
        embedding_model = None

        # If embedding_model_name is specified, find matching embedding
        if hasattr(self, "embedding_model_name") and self.embedding_model_name and self.embedding_model_name.strip():
            target_model_name = self.embedding_model_name.strip()
            self.log(f"Looking for embedding model: {target_model_name}")

            for emb_obj in embeddings_list:
                # Check all possible model identifiers (deployment, model, model_id, model_name)
                # Also check available_models list from EmbeddingsWithModels
                possible_names = []
                deployment = getattr(emb_obj, "deployment", None)
                model = getattr(emb_obj, "model", None)
                model_id = getattr(emb_obj, "model_id", None)
                model_name = getattr(emb_obj, "model_name", None)
                available_models_attr = getattr(emb_obj, "available_models", None)

                if deployment:
                    possible_names.append(str(deployment))
                if model:
                    possible_names.append(str(model))
                if model_id:
                    possible_names.append(str(model_id))
                if model_name:
                    possible_names.append(str(model_name))

                # Also add combined identifier
                if deployment and model and deployment != model:
                    possible_names.append(f"{deployment}:{model}")

                # Add all models from available_models dict
                if available_models_attr and isinstance(available_models_attr, dict):
                    possible_names.extend(
                        str(model_key).strip()
                        for model_key in available_models_attr
                        if model_key and str(model_key).strip()
                    )

                # Match if target matches any of the possible names
                if target_model_name in possible_names:
                    # Check if target is in available_models dict - use dedicated instance
                    if (
                        available_models_attr
                        and isinstance(available_models_attr, dict)
                        and target_model_name in available_models_attr
                    ):
                        # Use the dedicated embedding instance from the dict
                        selected_embedding = available_models_attr[target_model_name]
                        embedding_model = target_model_name
                        self.log(f"Found dedicated embedding instance for '{embedding_model}' in available_models dict")
                    else:
                        # Traditional identifier match
                        selected_embedding = emb_obj
                        embedding_model = self._get_embedding_model_name(emb_obj)
                        self.log(f"Found matching embedding model: {embedding_model} (matched on: {target_model_name})")
                    break

            if not selected_embedding:
                # Build detailed list of available embeddings with all their identifiers
                available_info = []
                for idx, emb in enumerate(embeddings_list):
                    emb_type = type(emb).__name__
                    identifiers = []
                    deployment = getattr(emb, "deployment", None)
                    model = getattr(emb, "model", None)
                    model_id = getattr(emb, "model_id", None)
                    model_name = getattr(emb, "model_name", None)
                    available_models_attr = getattr(emb, "available_models", None)

                    if deployment:
                        identifiers.append(f"deployment='{deployment}'")
                    if model:
                        identifiers.append(f"model='{model}'")
                    if model_id:
                        identifiers.append(f"model_id='{model_id}'")
                    if model_name:
                        identifiers.append(f"model_name='{model_name}'")

                    # Add combined identifier as an option
                    if deployment and model and deployment != model:
                        identifiers.append(f"combined='{deployment}:{model}'")

                    # Add available_models dict if present
                    if available_models_attr and isinstance(available_models_attr, dict):
                        identifiers.append(f"available_models={list(available_models_attr.keys())}")

                    available_info.append(
                        f"  [{idx}] {emb_type}: {', '.join(identifiers) if identifiers else 'No identifiers'}"
                    )

                msg = (
                    f"Embedding model '{target_model_name}' not found in available embeddings.\n\n"
                    f"Available embeddings:\n" + "\n".join(available_info) + "\n\n"
                    "Please set 'embedding_model_name' to one of the identifier values shown above "
                    "(use the value after the '=' sign, without quotes).\n"
                    "For duplicate deployments, use the 'combined' format.\n"
                    "Or leave it empty to use the first embedding."
                )
                raise ValueError(msg)
        else:
            # Use first embedding if no model name specified
            selected_embedding = embeddings_list[0]
            embedding_model = self._get_embedding_model_name(selected_embedding)
            self.log(f"No embedding_model_name specified, using first embedding: {embedding_model}")

        dynamic_field_name = get_embedding_field_name(embedding_model)

        logger.info(f"Selected embedding model for ingestion: '{embedding_model}'")
        self.log(f"Using embedding model for ingestion: {embedding_model}")
        self.log(f"Dynamic vector field: {dynamic_field_name}")

        # Log embedding details for debugging
        if hasattr(selected_embedding, "deployment"):
            logger.info(f"Embedding deployment: {selected_embedding.deployment}")
        if hasattr(selected_embedding, "model"):
            logger.info(f"Embedding model: {selected_embedding.model}")
        if hasattr(selected_embedding, "model_id"):
            logger.info(f"Embedding model_id: {selected_embedding.model_id}")
        if hasattr(selected_embedding, "dimensions"):
            logger.info(f"Embedding dimensions: {selected_embedding.dimensions}")
        if hasattr(selected_embedding, "available_models"):
            logger.info(f"Embedding available_models: {selected_embedding.available_models}")

        # No model switching needed - each model in available_models has its own dedicated instance
        # The selected_embedding is already configured correctly for the target model
        logger.info(f"Using embedding instance for '{embedding_model}' - pre-configured and ready to use")

        # Extract texts and metadata from documents
        texts = []
        metadatas = []
        # Process docs_metadata table input into a dict
        additional_metadata = {}
        logger.debug(f"[LF] Docs metadata {self.docs_metadata}")
        if hasattr(self, "docs_metadata") and self.docs_metadata:
            logger.info(f"[LF] Docs metadata {self.docs_metadata}")
            if isinstance(self.docs_metadata[-1], Data):
                logger.info(f"[LF] Docs metadata is a Data object {self.docs_metadata}")
                self.docs_metadata = self.docs_metadata[-1].data
                logger.info(f"[LF] Docs metadata is a Data object {self.docs_metadata}")
                additional_metadata.update(self.docs_metadata)
            else:
                for item in self.docs_metadata:
                    if isinstance(item, dict) and "key" in item and "value" in item:
                        additional_metadata[item["key"]] = item["value"]
        # Replace string "None" values with actual None
        for key, value in additional_metadata.items():
            if value == "None":
                additional_metadata[key] = None
        logger.info(f"[LF] Additional metadata {additional_metadata}")
        for doc_obj in docs:
            data_copy = json.loads(doc_obj.model_dump_json())
            text = data_copy.pop(doc_obj.text_key, doc_obj.default_value)
            texts.append(text)

            # Merge additional metadata from table input
            data_copy.update(additional_metadata)

            metadatas.append(data_copy)
        self.log(metadatas)

        # Generate embeddings with rate-limit-aware retry logic using tenacity
        from tenacity import (
            retry,
            retry_if_exception,
            stop_after_attempt,
            wait_exponential,
        )

        def is_rate_limit_error(exception: Exception) -> bool:
            """Check if exception is a rate limit error (429)."""
            error_str = str(exception).lower()
            return "429" in error_str or "rate_limit" in error_str or "rate limit" in error_str

        def is_other_retryable_error(exception: Exception) -> bool:
            """Check if exception is retryable but not a rate limit error."""
            # Retry on most exceptions except for specific non-retryable ones
            # Add other non-retryable exceptions here if needed
            return not is_rate_limit_error(exception)

        # Create retry decorator for rate limit errors (longer backoff)
        retry_on_rate_limit = retry(
            retry=retry_if_exception(is_rate_limit_error),
            stop=stop_after_attempt(5),
            wait=wait_exponential(multiplier=2, min=2, max=30),
            reraise=True,
            before_sleep=lambda retry_state: logger.warning(
                f"Rate limit hit for chunk (attempt {retry_state.attempt_number}/5), "
                f"backing off for {retry_state.next_action.sleep:.1f}s"
            ),
        )

        # Create retry decorator for other errors (shorter backoff)
        retry_on_other_errors = retry(
            retry=retry_if_exception(is_other_retryable_error),
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            reraise=True,
            before_sleep=lambda retry_state: logger.warning(
                f"Error embedding chunk (attempt {retry_state.attempt_number}/3), "
                f"retrying in {retry_state.next_action.sleep:.1f}s: {retry_state.outcome.exception()}"
            ),
        )

        def embed_chunk_with_retry(chunk_text: str, chunk_idx: int) -> list[float]:
            """Embed a single chunk with rate-limit-aware retry logic."""

            @retry_on_rate_limit
            @retry_on_other_errors
            def _embed(text: str) -> list[float]:
                return selected_embedding.embed_documents([text])[0]

            try:
                return _embed(chunk_text)
            except Exception as e:
                logger.error(
                    f"Failed to embed chunk {chunk_idx} after all retries: {e}",
                    error=str(e),
                )
                raise

        # Restrict concurrency for IBM/Watsonx models to avoid rate limits
        is_ibm = (embedding_model and "ibm" in str(embedding_model).lower()) or (
            selected_embedding and "watsonx" in type(selected_embedding).__name__.lower()
        )
        logger.debug(f"Is IBM: {is_ibm}")

        # For IBM models, use sequential processing with rate limiting
        # For other models, use parallel processing
        vectors: list[list[float]] = [None] * len(texts)

        if is_ibm:
            # Sequential processing with inter-request delay for IBM models
            inter_request_delay = 0.6  # ~1.67 req/s, safely under 2 req/s limit
            logger.info(f"Using sequential processing for IBM model with {inter_request_delay}s delay between requests")

            for idx, chunk in enumerate(texts):
                if idx > 0:
                    # Add delay between requests (but not before the first one)
                    time.sleep(inter_request_delay)
                vectors[idx] = embed_chunk_with_retry(chunk, idx)
        else:
            # Parallel processing for non-IBM models
            max_workers = min(max(len(texts), 1), 8)
            logger.debug(f"Using parallel processing with {max_workers} workers")

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(embed_chunk_with_retry, chunk, idx): idx for idx, chunk in enumerate(texts)}
                for future in as_completed(futures):
                    idx = futures[future]
                    vectors[idx] = future.result()

        if not vectors:
            self.log(f"No vectors generated from documents for model {embedding_model}.")
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
            vector_field=dynamic_field_name,  # Use dynamic field name
        )

        # Ensure index exists with baseline mapping (index.knn: true is required for vector search)
        try:
            if not client.indices.exists(index=self.index_name):
                self.log(f"Creating index '{self.index_name}' with base mapping")
                client.indices.create(index=self.index_name, body=mapping)
        except RequestError as creation_error:
            if creation_error.error == "resource_already_exists_exception":
                pass  # Index was created concurrently
            else:
                error_msg = str(creation_error).lower()
                if "invalid engine" in error_msg or "illegal_argument" in error_msg:
                    if "jvector" in error_msg:
                        msg = (
                            "The 'jvector' engine is not available in your OpenSearch installation. "
                            "Use 'nmslib' or 'faiss' for standard OpenSearch, or upgrade to 2.9+."
                        )
                        raise ValueError(msg) from creation_error
                    if "index.knn" in error_msg:
                        msg = (
                            "The index has index.knn: false. Delete the existing index and let the "
                            "component recreate it, or create a new index with a different name."
                        )
                        raise ValueError(msg) from creation_error
                logger.warning(f"Failed to create index '{self.index_name}': {creation_error}")
                raise

        # Ensure the dynamic field exists in the index
        self._ensure_embedding_field_mapping(
            client=client,
            index_name=self.index_name,
            field_name=dynamic_field_name,
            dim=dim,
            engine=engine,
            space_type=space_type,
            ef_construction=ef_construction,
            m=m,
        )

        self.log(f"Indexing {len(texts)} documents into '{self.index_name}' with model '{embedding_model}'...")
        logger.info(f"Will store embeddings in field: {dynamic_field_name}")
        logger.info(f"Will tag documents with embedding_model: {embedding_model}")

        # Use the bulk ingestion with model tracking
        return_ids = self._bulk_ingest_embeddings(
            client=client,
            index_name=self.index_name,
            embeddings=vectors,
            texts=texts,
            metadatas=metadatas,
            vector_field=dynamic_field_name,  # Use dynamic field name
            text_field="text",
            embedding_model=embedding_model,  # Track the model
            mapping=mapping,
            is_aoss=is_aoss,
        )
        self.log(metadatas)

        logger.info(
            f"Ingestion complete: Successfully indexed {len(return_ids)} documents with model '{embedding_model}'"
        )
        self.log(f"Successfully indexed {len(return_ids)} documents with model {embedding_model}.")