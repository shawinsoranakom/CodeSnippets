async def update_state(self, state: CrawlState, new_results: List[CrawlResult]) -> None:
        """Update embeddings and coverage metrics with deduplication"""
        from .utils import get_text_embeddings


        # Extract text from results
        new_texts = []
        valid_results = []
        for result in new_results:
            content = result.markdown.raw_markdown if hasattr(result, 'markdown') and result.markdown else ""
            if content:  # Only process non-empty content
                new_texts.append(content[:5000])  # Limit text length
                valid_results.append(result)

        if not new_texts:
            return

        # Get embeddings for new texts
        embedding_llm_config = self._get_embedding_llm_config_dict()      
        new_embeddings = await get_text_embeddings(new_texts, embedding_llm_config, self.embedding_model)

        # Deduplicate embeddings before adding to KB
        if state.kb_embeddings is None:
            # First batch - no deduplication needed
            state.kb_embeddings = new_embeddings
            deduplicated_indices = list(range(len(new_embeddings)))
        else:
            # Check for duplicates using vectorized similarity
            deduplicated_embeddings = []
            deduplicated_indices = []

            for i, new_emb in enumerate(new_embeddings):
                # Compute similarities with existing KB
                new_emb_normalized = new_emb / np.linalg.norm(new_emb)
                kb_normalized = state.kb_embeddings / np.linalg.norm(state.kb_embeddings, axis=1, keepdims=True)
                similarities = np.dot(kb_normalized, new_emb_normalized)

                # Only add if not too similar to existing content
                if np.max(similarities) < self._kb_similarity_threshold:
                    deduplicated_embeddings.append(new_emb)
                    deduplicated_indices.append(i)

            # Add deduplicated embeddings
            if deduplicated_embeddings:
                state.kb_embeddings = np.vstack([state.kb_embeddings, np.array(deduplicated_embeddings)])

        # Update crawl order only for non-duplicate results
        for idx in deduplicated_indices:
            state.crawl_order.append(valid_results[idx].url)

        # Invalidate distance matrix cache since KB changed
        self._kb_embeddings_hash = None
        self._distance_matrix_cache = None

        # Update coverage shape if needed
        if hasattr(state, 'query_embeddings') and state.query_embeddings is not None:
            state.coverage_shape = self.compute_coverage_shape(state.query_embeddings, self.config.alpha_shape_alpha if hasattr(self, 'config') else 0.5)