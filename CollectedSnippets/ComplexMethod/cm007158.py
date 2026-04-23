def search(self, query: str | None = None) -> list[dict[str, Any]]:
        """Perform hybrid search combining vector similarity and keyword matching.

        This method executes a sophisticated search that combines:
        - K-nearest neighbor (KNN) vector similarity search (70% weight)
        - Multi-field keyword search with fuzzy matching (30% weight)
        - Optional filtering and score thresholds
        - Aggregations for faceted search results

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

        # Parse optional filter expression (can be either A or B shape; see _coerce_filter_clauses)
        filter_obj = None
        if getattr(self, "filter_expression", "") and self.filter_expression.strip():
            try:
                filter_obj = json.loads(self.filter_expression)
            except json.JSONDecodeError as e:
                msg = f"Invalid filter_expression JSON: {e}"
                raise ValueError(msg) from e

        if not self.embedding:
            msg = "Embedding is required to run hybrid search (KNN + keyword)."
            raise ValueError(msg)

        # Embed the query
        vec = self.embedding.embed_query(q)

        # Build filter clauses (accept both shapes)
        filter_clauses = self._coerce_filter_clauses(filter_obj)

        # Respect the tool's limit/threshold defaults
        limit = (filter_obj or {}).get("limit", self.number_of_results)
        score_threshold = (filter_obj or {}).get("score_threshold", 0)

        # Build the same hybrid body as your SearchService
        body = {
            "query": {
                "bool": {
                    "should": [
                        {
                            "knn": {
                                self.vector_field: {
                                    "vector": vec,
                                    "k": 10,  # fixed to match the tool
                                    "boost": 0.7,
                                }
                            }
                        },
                        {
                            "multi_match": {
                                "query": q,
                                "fields": ["text^2", "filename^1.5"],
                                "type": "best_fields",
                                "fuzziness": "AUTO",
                                "boost": 0.3,
                            }
                        },
                    ],
                    "minimum_should_match": 1,
                }
            },
            "aggs": {
                "data_sources": {"terms": {"field": "filename", "size": 20}},
                "document_types": {"terms": {"field": "mimetype", "size": 10}},
                "owners": {"terms": {"field": "owner", "size": 10}},
            },
            "_source": [
                "filename",
                "mimetype",
                "page",
                "text",
                "source_url",
                "owner",
                "allowed_users",
                "allowed_groups",
            ],
            "size": limit,
        }
        if filter_clauses:
            body["query"]["bool"]["filter"] = filter_clauses

        if isinstance(score_threshold, (int, float)) and score_threshold > 0:
            # top-level min_score (matches your tool)
            body["min_score"] = score_threshold

        resp = client.search(index=self.index_name, body=body)
        hits = resp.get("hits", {}).get("hits", [])
        return [
            {
                "page_content": hit["_source"].get("text", ""),
                "metadata": {k: v for k, v in hit["_source"].items() if k != "text"},
                "score": hit.get("_score"),
            }
            for hit in hits
        ]