def search(self, query: str | None = None) -> list[dict[str, Any]]:
        """Perform multi-model hybrid search combining multiple vector similarities and keyword matching.

        This method executes a sophisticated search that:
        1. Auto-detects all embedding models present in the index
        2. Generates query embeddings for ALL detected models in parallel
        3. Combines multiple KNN queries using dis_max (picks best match)
        4. Adds keyword search with fuzzy matching (30% weight)
        5. Applies optional filtering and score thresholds
        6. Returns aggregations for faceted search

        Search weights:
        - Semantic search (dis_max across all models): 70%
        - Keyword search: 30%

        Args:
            query: Search query string (used for both vector embedding and keyword search)

        Returns:
            List of search results with page_content, metadata, and relevance scores

        Raises:
            ValueError: If embedding component is not provided or filter JSON is invalid
        """
        logger.info(self.ingest_data)
        client = self.build_client()
        q = (query or "").strip()

        # Parse optional filter expression
        filter_obj = self._parse_filter_expression()

        if not self.embedding:
            msg = "Embedding is required to run hybrid search (KNN + keyword)."
            raise ValueError(msg)

        # Check if embedding is None (fail-safe mode)
        if self.embedding is None or (isinstance(self.embedding, list) and all(e is None for e in self.embedding)):
            logger.error("Embedding returned None (fail-safe mode enabled). Cannot perform search.")
            return []

        # Build filter clauses first so we can use them in model detection
        filter_clauses = self._coerce_filter_clauses(filter_obj)

        # Detect available embedding models in the index (scoped by filters)
        available_models = self._detect_available_models(client, filter_clauses)

        if not available_models:
            logger.warning("No embedding models found in index, using current model")
            available_models = [self._get_embedding_model_name()]

        # Generate embeddings for ALL detected models
        query_embeddings = {}

        # Normalize embedding to list
        embeddings_list = self.embedding if isinstance(self.embedding, list) else [self.embedding]
        # Filter out None values (fail-safe mode)
        embeddings_list = [e for e in embeddings_list if e is not None]

        if not embeddings_list:
            logger.error(
                "No valid embeddings available after filtering None values (fail-safe mode). Cannot perform search."
            )
            return []

        # Create a comprehensive map of model names to embedding objects
        # Check all possible identifiers (deployment, model, model_id, model_name)
        # Also leverage available_models list from EmbeddingsWithModels
        # Handle duplicate identifiers by creating combined keys
        embedding_by_model = {}
        identifier_conflicts = {}  # Track which identifiers have conflicts

        for idx, emb_obj in enumerate(embeddings_list):
            # Get all possible identifiers for this embedding
            identifiers = []
            deployment = getattr(emb_obj, "deployment", None)
            model = getattr(emb_obj, "model", None)
            model_id = getattr(emb_obj, "model_id", None)
            model_name = getattr(emb_obj, "model_name", None)
            dimensions = getattr(emb_obj, "dimensions", None)
            available_models_attr = getattr(emb_obj, "available_models", None)

            logger.info(
                f"Embedding object {idx}: deployment={deployment}, model={model}, "
                f"model_id={model_id}, model_name={model_name}, dimensions={dimensions}, "
                f"available_models={available_models_attr}"
            )

            # If this embedding has available_models dict, map all models to their dedicated instances
            if available_models_attr and isinstance(available_models_attr, dict):
                logger.info(
                    f"Embedding object {idx} provides {len(available_models_attr)} models via available_models dict"
                )
                for model_name_key, dedicated_embedding in available_models_attr.items():
                    if model_name_key and str(model_name_key).strip():
                        model_str = str(model_name_key).strip()
                        if model_str not in embedding_by_model:
                            # Use the dedicated embedding instance from the dict
                            embedding_by_model[model_str] = dedicated_embedding
                            logger.info(f"Mapped available model '{model_str}' to dedicated embedding instance")
                        else:
                            # Conflict detected - track it
                            if model_str not in identifier_conflicts:
                                identifier_conflicts[model_str] = [embedding_by_model[model_str]]
                            identifier_conflicts[model_str].append(dedicated_embedding)
                            logger.warning(f"Available model '{model_str}' has conflict - used by multiple embeddings")

            # Also map traditional identifiers (for backward compatibility)
            if deployment:
                identifiers.append(str(deployment))
            if model:
                identifiers.append(str(model))
            if model_id:
                identifiers.append(str(model_id))
            if model_name:
                identifiers.append(str(model_name))

            # Map all identifiers to this embedding object
            for identifier in identifiers:
                if identifier not in embedding_by_model:
                    embedding_by_model[identifier] = emb_obj
                    logger.info(f"Mapped identifier '{identifier}' to embedding object {idx}")
                else:
                    # Conflict detected - track it
                    if identifier not in identifier_conflicts:
                        identifier_conflicts[identifier] = [embedding_by_model[identifier]]
                    identifier_conflicts[identifier].append(emb_obj)
                    logger.warning(f"Identifier '{identifier}' has conflict - used by multiple embeddings")

            # For embeddings with model+deployment, create combined identifier
            # This helps when deployment is the same but model differs
            if deployment and model and deployment != model:
                combined_id = f"{deployment}:{model}"
                if combined_id not in embedding_by_model:
                    embedding_by_model[combined_id] = emb_obj
                    logger.info(f"Created combined identifier '{combined_id}' for embedding object {idx}")

        # Log conflicts
        if identifier_conflicts:
            logger.warning(
                f"Found {len(identifier_conflicts)} conflicting identifiers. "
                f"Consider using combined format 'deployment:model' or specifying unique model names."
            )
            for conflict_id, emb_list in identifier_conflicts.items():
                logger.warning(f"  Conflict on '{conflict_id}': {len(emb_list)} embeddings use this identifier")

        logger.info(f"Generating embeddings for {len(available_models)} models in index")
        logger.info(f"Available embedding identifiers: {list(embedding_by_model.keys())}")
        self.log(f"[SEARCH] Models detected in index: {available_models}")
        self.log(f"[SEARCH] Available embedding identifiers: {list(embedding_by_model.keys())}")

        # Track matching status for debugging
        matched_models = []
        unmatched_models = []

        for model_name in available_models:
            try:
                # Check if we have an embedding object for this model
                if model_name in embedding_by_model:
                    # Use the matching embedding object directly
                    emb_obj = embedding_by_model[model_name]
                    emb_deployment = getattr(emb_obj, "deployment", None)
                    emb_model = getattr(emb_obj, "model", None)
                    emb_model_id = getattr(emb_obj, "model_id", None)
                    emb_dimensions = getattr(emb_obj, "dimensions", None)
                    emb_available_models = getattr(emb_obj, "available_models", None)

                    logger.info(
                        f"Using embedding object for model '{model_name}': "
                        f"deployment={emb_deployment}, model={emb_model}, model_id={emb_model_id}, "
                        f"dimensions={emb_dimensions}"
                    )

                    # Check if this is a dedicated instance from available_models dict
                    if emb_available_models and isinstance(emb_available_models, dict):
                        logger.info(
                            f"Model '{model_name}' using dedicated instance from available_models dict "
                            f"(pre-configured with correct model and dimensions)"
                        )

                    # Use the embedding instance directly - no model switching needed!
                    vec = emb_obj.embed_query(q)
                    query_embeddings[model_name] = vec
                    matched_models.append(model_name)
                    logger.info(f"Generated embedding for model: {model_name} (actual dimensions: {len(vec)})")
                    self.log(f"[MATCH] Model '{model_name}' - generated {len(vec)}-dim embedding")
                else:
                    # No matching embedding found for this model
                    unmatched_models.append(model_name)
                    logger.warning(
                        f"No matching embedding found for model '{model_name}'. "
                        f"This model will be skipped. Available identifiers: {list(embedding_by_model.keys())}"
                    )
                    self.log(f"[NO MATCH] Model '{model_name}' - available: {list(embedding_by_model.keys())}")
            except (RuntimeError, ValueError, ConnectionError, TimeoutError, AttributeError, KeyError) as e:
                logger.warning(f"Failed to generate embedding for {model_name}: {e}")
                self.log(f"[ERROR] Embedding generation failed for '{model_name}': {e}")

        # Log summary of model matching
        logger.info(f"Model matching summary: {len(matched_models)} matched, {len(unmatched_models)} unmatched")
        self.log(f"[SUMMARY] Model matching: {len(matched_models)} matched, {len(unmatched_models)} unmatched")
        if unmatched_models:
            self.log(f"[WARN] Unmatched models in index: {unmatched_models}")

        if not query_embeddings:
            msg = (
                f"Failed to generate embeddings for any model. "
                f"Index has models: {available_models}, but no matching embedding objects found. "
                f"Available embedding identifiers: {list(embedding_by_model.keys())}"
            )
            self.log(f"[FAIL] Search failed: {msg}")
            raise ValueError(msg)

        index_properties = self._get_index_properties(client)
        legacy_vector_field = getattr(self, "vector_field", "chunk_embedding")

        # Build KNN queries for each model
        embedding_fields: list[str] = []
        knn_queries_with_candidates = []
        knn_queries_without_candidates = []

        raw_num_candidates = getattr(self, "num_candidates", 1000)
        try:
            num_candidates = int(raw_num_candidates) if raw_num_candidates is not None else 0
        except (TypeError, ValueError):
            num_candidates = 0
        use_num_candidates = num_candidates > 0

        for model_name, embedding_vector in query_embeddings.items():
            field_name = get_embedding_field_name(model_name)
            selected_field = field_name
            vector_dim = len(embedding_vector)

            # Only use the expected dynamic field - no legacy fallback
            # This prevents dimension mismatches between models
            if not self._is_knn_vector_field(index_properties, selected_field):
                logger.warning(
                    f"Skipping model {model_name}: field '{field_name}' is not mapped as knn_vector. "
                    f"Documents must be indexed with this embedding model before querying."
                )
                self.log(f"[SKIP] Field '{selected_field}' not a knn_vector - skipping model '{model_name}'")
                continue

            # Validate vector dimensions match the field dimensions
            field_dim = self._get_field_dimension(index_properties, selected_field)
            if field_dim is not None and field_dim != vector_dim:
                logger.error(
                    f"Dimension mismatch for model '{model_name}': "
                    f"Query vector has {vector_dim} dimensions but field '{selected_field}' expects {field_dim}. "
                    f"Skipping this model to prevent search errors."
                )
                self.log(f"[DIM MISMATCH] Model '{model_name}': query={vector_dim} vs field={field_dim} - skipping")
                continue

            logger.info(
                f"Adding KNN query for model '{model_name}': field='{selected_field}', "
                f"query_dims={vector_dim}, field_dims={field_dim or 'unknown'}"
            )
            embedding_fields.append(selected_field)

            base_query = {
                "knn": {
                    selected_field: {
                        "vector": embedding_vector,
                        "k": 50,
                    }
                }
            }

            if use_num_candidates:
                query_with_candidates = copy.deepcopy(base_query)
                query_with_candidates["knn"][selected_field]["num_candidates"] = num_candidates
            else:
                query_with_candidates = base_query

            knn_queries_with_candidates.append(query_with_candidates)
            knn_queries_without_candidates.append(base_query)

        if not knn_queries_with_candidates:
            # No valid fields found - this can happen when:
            # 1. Index is empty (no documents yet)
            # 2. Embedding model has changed and field doesn't exist yet
            # Return empty results instead of failing
            logger.warning(
                "No valid knn_vector fields found for embedding models. "
                "This may indicate an empty index or missing field mappings. "
                "Returning empty search results."
            )
            self.log(
                f"[WARN] No valid KNN queries could be built. "
                f"Query embeddings generated: {list(query_embeddings.keys())}, "
                f"but no matching knn_vector fields found in index."
            )
            return []

        # Build exists filter - document must have at least one embedding field
        exists_any_embedding = {
            "bool": {"should": [{"exists": {"field": f}} for f in set(embedding_fields)], "minimum_should_match": 1}
        }

        # Combine user filters with exists filter
        all_filters = [*filter_clauses, exists_any_embedding]

        # Get limit and score threshold
        limit = self._resolve_limit(filter_obj, default_limit=self.number_of_results)
        score_threshold = self._resolve_score_threshold(filter_obj)

        # Determine the best aggregation field for filename based on index mapping
        filename_agg_field = self._get_filename_agg_field(index_properties)

        # Build multi-model hybrid query
        body = {
            "query": {
                "bool": {
                    "should": [
                        {
                            "dis_max": {
                                "tie_breaker": 0.0,  # Take only the best match, no blending
                                "boost": 0.7,  # 70% weight for semantic search
                                "queries": knn_queries_with_candidates,
                            }
                        },
                        {
                            "multi_match": {
                                "query": q,
                                "fields": ["text^2", "filename^1.5"],
                                "type": "best_fields",
                                "fuzziness": "AUTO",
                                "boost": 0.3,  # 30% weight for keyword search
                            }
                        },
                    ],
                    "minimum_should_match": 1,
                    "filter": all_filters,
                }
            },
            "aggs": {
                "data_sources": {"terms": {"field": filename_agg_field, "size": 20}},
                "document_types": {"terms": {"field": "mimetype", "size": 10}},
                "owners": {"terms": {"field": "owner", "size": 10}},
                "embedding_models": {"terms": {"field": "embedding_model", "size": 10}},
            },
            "_source": [
                "filename",
                "mimetype",
                "page",
                "text",
                "source_url",
                "owner",
                "embedding_model",
                "allowed_users",
                "allowed_groups",
            ],
            "size": limit,
        }

        if score_threshold is not None:
            body["min_score"] = score_threshold

        logger.info(
            f"Executing multi-model hybrid search with {len(knn_queries_with_candidates)} embedding models: "
            f"{list(query_embeddings.keys())}"
        )
        self.log(f"[EXEC] Executing search with {len(knn_queries_with_candidates)} KNN queries, limit={limit}")
        self.log(f"[EXEC] Embedding models used: {list(query_embeddings.keys())}")
        self.log(f"[EXEC] KNN fields being queried: {embedding_fields}")

        try:
            resp = client.search(index=self.index_name, body=body, params={"terminate_after": 0})
        except RequestError as e:
            error_message = str(e)
            lowered = error_message.lower()
            if use_num_candidates and "num_candidates" in lowered:
                logger.warning(
                    "Retrying search without num_candidates parameter due to cluster capabilities",
                    error=error_message,
                )
                fallback_body = copy.deepcopy(body)
                try:
                    fallback_body["query"]["bool"]["should"][0]["dis_max"]["queries"] = knn_queries_without_candidates
                except (KeyError, IndexError, TypeError) as inner_err:
                    raise e from inner_err
                resp = client.search(
                    index=self.index_name,
                    body=fallback_body,
                    params={"terminate_after": 0},
                )
            elif "knn_vector" in lowered or ("field" in lowered and "knn" in lowered):
                fallback_vector = next(iter(query_embeddings.values()), None)
                if fallback_vector is None:
                    raise
                fallback_field = legacy_vector_field or "chunk_embedding"
                logger.warning(
                    "KNN search failed for dynamic fields; falling back to legacy field '%s'.",
                    fallback_field,
                )
                fallback_body = copy.deepcopy(body)
                fallback_body["query"]["bool"]["filter"] = filter_clauses
                knn_fallback = {
                    "knn": {
                        fallback_field: {
                            "vector": fallback_vector,
                            "k": 50,
                        }
                    }
                }
                if use_num_candidates:
                    knn_fallback["knn"][fallback_field]["num_candidates"] = num_candidates
                fallback_body["query"]["bool"]["should"][0]["dis_max"]["queries"] = [knn_fallback]
                resp = client.search(
                    index=self.index_name,
                    body=fallback_body,
                    params={"terminate_after": 0},
                )
            else:
                raise
        hits = resp.get("hits", {}).get("hits", [])

        logger.info(f"Found {len(hits)} results")
        self.log(f"[RESULT] Search complete: {len(hits)} results found")

        if len(hits) == 0:
            self.log(
                f"[EMPTY] Debug info: "
                f"models_in_index={available_models}, "
                f"matched_models={matched_models}, "
                f"knn_fields={embedding_fields}, "
                f"filters={len(filter_clauses)} clauses"
            )

        return [
            {
                "page_content": hit["_source"].get("text", ""),
                "metadata": {k: v for k, v in hit["_source"].items() if k != "text"},
                "score": hit.get("_score"),
            }
            for hit in hits
        ]