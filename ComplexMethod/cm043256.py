async def validate_coverage(self, state: CrawlState) -> float:
        """Validate coverage using held-out queries with caching"""
        if not hasattr(self, '_validation_queries') or not self._validation_queries:
            return state.metrics.get('confidence', 0.0)

        import numpy as np

        # Cache validation embeddings (only embed once!)
        if self._validation_embeddings_cache is None:
            self._validation_embeddings_cache = await self._get_embeddings(self._validation_queries)

        val_embeddings = self._validation_embeddings_cache

        # Use vectorized distance computation
        if state.kb_embeddings is None or len(state.kb_embeddings) == 0:
            return 0.0

        # Compute distance matrix for validation queries
        distance_matrix = self._compute_distance_matrix(val_embeddings, state.kb_embeddings)

        if distance_matrix is None:
            return 0.0

        # Find minimum distance for each validation query (vectorized)
        min_distances = np.min(distance_matrix, axis=1)

        # Compute scores using same exponential as training
        k_exp = self.config.embedding_k_exp if hasattr(self, 'config') else 1.0
        scores = np.exp(-k_exp * min_distances)

        validation_confidence = np.mean(scores)
        state.metrics['validation_confidence'] = validation_confidence

        return validation_confidence