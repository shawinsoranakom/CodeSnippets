async def should_stop(self, state: CrawlState, config: AdaptiveConfig) -> bool:
        """Stop based on learning curve convergence"""
        confidence = state.metrics.get('confidence', 0.0)

        # Basic limits
        if len(state.crawled_urls) >= config.max_pages or not state.pending_links:
            return True

        # Track confidence history
        if not hasattr(state, 'confidence_history'):
            state.confidence_history = []

        state.confidence_history.append(confidence)

        # Need at least 3 iterations to check convergence
        if len(state.confidence_history) < 2:
            return False

        improvement_diffs = list(zip(state.confidence_history[:-1], state.confidence_history[1:]))

        # Calculate average improvement
        avg_improvement = sum(abs(b - a) for a, b in improvement_diffs) / len(improvement_diffs)
        state.metrics['avg_improvement'] = avg_improvement

        min_relative_improvement = self.config.embedding_min_relative_improvement * confidence if hasattr(self, 'config') else 0.1 * confidence
        if avg_improvement < min_relative_improvement:
            # Converged - validate before stopping
            val_score = await self.validate_coverage(state)

            # Only stop if validation is reasonable
            validation_min = self.config.embedding_validation_min_score if hasattr(self, 'config') else 0.4
            if val_score > validation_min:
                state.metrics['stopped_reason'] = 'converged_validated'
                self._validation_passed = True
                return True
            else:
                state.metrics['stopped_reason'] = 'low_validation'
                # Continue crawling despite convergence

        return False