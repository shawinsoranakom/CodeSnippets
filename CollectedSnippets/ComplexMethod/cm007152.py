def _detect_available_models(self, client: OpenSearch, filter_clauses: list[dict] | None = None) -> list[str]:
        """Detect which embedding models have documents in the index.

        Uses aggregation to find all unique embedding_model values, optionally
        filtered to only documents matching the user's filter criteria.

        Args:
            client: OpenSearch client instance
            filter_clauses: Optional filter clauses to scope model detection

        Returns:
            List of embedding model names found in the index
        """
        try:
            agg_query = {"size": 0, "aggs": {"embedding_models": {"terms": {"field": "embedding_model", "size": 10}}}}

            # Apply filters to model detection if any exist
            if filter_clauses:
                agg_query["query"] = {"bool": {"filter": filter_clauses}}

            logger.debug(f"Model detection query: {agg_query}")
            result = client.search(
                index=self.index_name,
                body=agg_query,
                params={"terminate_after": 0},
            )
            buckets = result.get("aggregations", {}).get("embedding_models", {}).get("buckets", [])
            models = [b["key"] for b in buckets if b["key"]]

            # Log detailed bucket info for debugging
            logger.info(
                f"Detected embedding models in corpus: {models}"
                + (f" (with {len(filter_clauses)} filters)" if filter_clauses else "")
            )
            if not models:
                total_hits = result.get("hits", {}).get("total", {})
                total_count = total_hits.get("value", 0) if isinstance(total_hits, dict) else total_hits
                logger.warning(
                    f"No embedding_model values found in index '{self.index_name}'. "
                    f"Total docs in index: {total_count}. "
                    f"This may indicate documents were indexed without the embedding_model field."
                )
        except (OpenSearchException, KeyError, ValueError) as e:
            logger.warning(f"Failed to detect embedding models: {e}")
            # Fallback to current model
            fallback_model = self._get_embedding_model_name()
            logger.info(f"Using fallback model: {fallback_model}")
            return [fallback_model]
        else:
            return models