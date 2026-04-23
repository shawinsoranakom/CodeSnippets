def raw_search(self, query: str | dict | None = None) -> Data:
        """Execute a raw OpenSearch query against the target index.

        Args:
            query (dict[str, Any]): The OpenSearch query DSL dictionary.

        Returns:
            Data: Search results as a Data object.

        Raises:
            ValueError: If 'query' is not a valid OpenSearch query (must be a non-empty dict).
        """
        raw_query = query if query is not None else self.search_query

        if raw_query is None or (isinstance(raw_query, str) and not raw_query.strip()):
            self.log("No query provided for raw search - returning empty results")
            return Data(data={})

        if isinstance(raw_query, dict):
            query_body = copy.deepcopy(raw_query)
        elif isinstance(raw_query, str):
            s = raw_query.strip()

            # First, optimistically try to parse as JSON DSL
            try:
                query_body = json.loads(s)
            except json.JSONDecodeError:
                # Fallback: treat as a basic text query over common fields
                query_body = {
                    "query": {
                        "multi_match": {
                            "query": s,
                            "fields": ["text^2", "filename^1.5"],
                            "type": "best_fields",
                            "fuzziness": "AUTO",
                        }
                    }
                }
        else:
            msg = f"Unsupported raw_search query type: {type(raw_query)!r}"
            raise TypeError(msg)

        filter_obj = self._parse_filter_expression()
        filter_clauses = self._coerce_filter_clauses(filter_obj)

        if filter_clauses:
            if "query" in query_body:
                original_query = query_body["query"]
                query_body["query"] = {
                    "bool": {
                        "must": [original_query],
                        "filter": filter_clauses,
                    }
                }
            else:
                query_body["query"] = {
                    "bool": {
                        "must": [{"match_all": {}}],
                        "filter": filter_clauses,
                    }
                }

        if filter_obj:
            # Apply limit if not already set in the raw query
            if "size" not in query_body:
                limit = self._resolve_limit(filter_obj, default_limit=None)
                if limit is not None:
                    query_body["size"] = limit

            # Apply score_threshold / scoreThreshold as min_score if not already set
            if "min_score" not in query_body:
                score_threshold = self._resolve_score_threshold(filter_obj)
                if score_threshold is not None:
                    query_body["min_score"] = score_threshold

        client = self.build_client()
        logger.info(f"query: {query_body}")
        resp = client.search(
            index=self.index_name,
            body=query_body,
            params={"terminate_after": 0},
        )
        # Remove any _source keys whose value is a list of floats (embedding vectors)
        # Minimum length threshold to identify embedding vectors
        min_vector_length = 100

        def is_vector(val):
            # Accepts if it's a list of numbers (float or int) and has reasonable vector length
            return (
                isinstance(val, list) and len(val) > min_vector_length and all(isinstance(x, (float, int)) for x in val)
            )

        if "hits" in resp and "hits" in resp["hits"]:
            for hit in resp["hits"]["hits"]:
                source = hit.get("_source")
                if isinstance(source, dict):
                    keys_to_remove = [k for k, v in source.items() if is_vector(v)]
                    for k in keys_to_remove:
                        source.pop(k)
        logger.info(f"Raw search response (all embedding vectors removed): {resp}")
        return Data(**resp)