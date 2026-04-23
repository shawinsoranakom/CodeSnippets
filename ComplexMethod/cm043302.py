async def _apply_bm25_scoring(self, results: List[Dict[str, Any]], config: "SeedingConfig") -> List[Dict[str, Any]]:
        """Apply BM25 scoring to results that have head_data."""
        if not HAS_BM25:
            self._log("warning", "BM25 scoring requested but rank_bm25 not available", tag="URL_SEED")
            return results

        # Extract text contexts from head data
        text_contexts = []
        valid_results = []

        for result in results:
            if result.get("status") == "valid" and result.get("head_data"):
                text_context = self._extract_text_context(result["head_data"])
                if text_context:
                    text_contexts.append(text_context)
                    valid_results.append(result)
                else:
                    # Use URL-based scoring as fallback
                    score = self._calculate_url_relevance_score(config.query, result["url"])
                    result["relevance_score"] = float(score)
            elif result.get("status") == "valid":
                # No head data but valid URL - use URL-based scoring
                score = self._calculate_url_relevance_score(config.query, result["url"])
                result["relevance_score"] = float(score)

        # Calculate BM25 scores for results with text context
        if text_contexts and valid_results:
            scores = await asyncio.to_thread(self._calculate_bm25_score, config.query, text_contexts)
            for i, result in enumerate(valid_results):
                if i < len(scores):
                    result["relevance_score"] = float(scores[i])

        return results