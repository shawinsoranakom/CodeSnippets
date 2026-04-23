async def run(
        self, args: Union[str, Dict[str, Any], SearchQuery], cancellation_token: Optional[CancellationToken] = None
    ) -> SearchResults:
        """Execute a search against the Azure AI Search index.

        Args:
            args: Search query text or SearchQuery object
            cancellation_token: Optional token to cancel the operation

        Returns:
            SearchResults: Container with search results and metadata

        Raises:
            ValueError: If the search query is empty or invalid
            ValueError: If there is an authentication error or other search issue
            asyncio.CancelledError: If the operation is cancelled
        """
        if isinstance(args, str):
            if not args.strip():
                raise ValueError("Search query cannot be empty")
            search_query = SearchQuery(query=args)
        elif isinstance(args, dict) and "query" in args:
            search_query = SearchQuery(query=args["query"])
        elif isinstance(args, SearchQuery):
            search_query = args
        else:
            raise ValueError("Invalid search query format. Expected string, dict with 'query', or SearchQuery")

        if cancellation_token is not None and cancellation_token.is_cancelled():
            raise asyncio.CancelledError("Operation cancelled")

        cache_key = ""
        if self.search_config.enable_caching:
            cache_key_parts = [
                search_query.query,
                str(self.search_config.top),
                self.search_config.query_type,
                ",".join(sorted(self.search_config.search_fields or [])),
                ",".join(sorted(self.search_config.select_fields or [])),
                ",".join(sorted(self.search_config.vector_fields or [])),
                str(self.search_config.filter or ""),
                str(self.search_config.semantic_config_name or ""),
            ]
            cache_key = ":".join(filter(None, cache_key_parts))
            if cache_key in self._cache:
                cache_entry = self._cache[cache_key]
                cache_age = time.time() - cache_entry["timestamp"]
                if cache_age < self.search_config.cache_ttl_seconds:
                    logger.debug(f"Using cached results for query: {search_query.query}")
                    return SearchResults(
                        results=[
                            SearchResult(score=r.score, content=r.content, metadata=r.metadata)
                            for r in cache_entry["results"]
                        ]
                    )

        try:
            search_kwargs: Dict[str, Any] = {}

            if self.search_config.query_type != "vector":
                search_kwargs["search_text"] = search_query.query
                search_kwargs["query_type"] = self.search_config.query_type

                if self.search_config.search_fields:
                    search_kwargs["search_fields"] = self.search_config.search_fields  # type: ignore[assignment]

                if self.search_config.query_type == "semantic" and self.search_config.semantic_config_name:
                    search_kwargs["semantic_configuration_name"] = self.search_config.semantic_config_name

            if self.search_config.select_fields:
                search_kwargs["select"] = self.search_config.select_fields  # type: ignore[assignment]
            if self.search_config.filter:
                search_kwargs["filter"] = str(self.search_config.filter)
            if self.search_config.top is not None:
                search_kwargs["top"] = self.search_config.top  # type: ignore[assignment]

            if self.search_config.vector_fields and len(self.search_config.vector_fields) > 0:
                if not search_query.query:
                    raise ValueError("Query text cannot be empty for vector search operations")

                use_client_side_embeddings = bool(
                    self.search_config.embedding_model and self.search_config.embedding_provider
                )

                vector_queries: List[Union[VectorizedQuery, VectorizableTextQuery]] = []
                if use_client_side_embeddings:
                    from azure.search.documents.models import VectorizedQuery

                    embedding_vector: List[float] = await self._get_embedding(search_query.query)
                    for field_spec in self.search_config.vector_fields:
                        fields = field_spec if isinstance(field_spec, str) else ",".join(field_spec)
                        vector_queries.append(
                            VectorizedQuery(
                                vector=embedding_vector,
                                k_nearest_neighbors=self.search_config.top or 5,
                                fields=fields,
                                kind="vector",
                            )
                        )
                else:
                    from azure.search.documents.models import VectorizableTextQuery

                    for field in self.search_config.vector_fields:
                        fields = field if isinstance(field, str) else ",".join(field)
                        vector_queries.append(
                            VectorizableTextQuery(  # type: ignore
                                text=search_query.query,
                                k_nearest_neighbors=self.search_config.top or 5,
                                fields=fields,
                                kind="vectorizable",
                            )
                        )

                search_kwargs["vector_queries"] = vector_queries  # type: ignore[assignment]

            if cancellation_token is not None:
                dummy_task = asyncio.create_task(asyncio.sleep(60))
                cancellation_token.link_future(dummy_task)

                def is_cancelled() -> bool:
                    return cancellation_token.is_cancelled()
            else:

                def is_cancelled() -> bool:
                    return False

            client = await self._get_client()
            search_results: SearchResultsIterable = await client.search(**search_kwargs)  # type: ignore[arg-type]

            results: List[SearchResult] = []
            async for doc in search_results:
                if is_cancelled():
                    raise asyncio.CancelledError("Operation was cancelled")

                try:
                    metadata: Dict[str, Any] = {}
                    content: Dict[str, Any] = {}

                    for key, value in doc.items():
                        if isinstance(key, str) and key.startswith(("@", "_")):
                            metadata[key] = value
                        else:
                            content[str(key)] = value

                    score = float(metadata.get("@search.score", 0.0))
                    results.append(SearchResult(score=score, content=content, metadata=metadata))
                except Exception as e:
                    logger.warning(f"Error processing search document: {e}")
                    continue

            if self.search_config.enable_caching:
                self._cache[cache_key] = {"results": results, "timestamp": time.time()}

            return SearchResults(results=results)

        except asyncio.CancelledError:
            raise
        except Exception as e:
            error_msg = str(e)
            if isinstance(e, HttpResponseError):
                if hasattr(e, "message") and e.message:
                    error_msg = e.message

            if "not found" in error_msg.lower():
                raise ValueError(f"Index '{self.search_config.index_name}' not found.") from e
            elif "unauthorized" in error_msg.lower() or "401" in error_msg:
                raise ValueError(f"Authentication failed: {error_msg}") from e
            else:
                raise ValueError(f"Error from Azure AI Search: {error_msg}") from e