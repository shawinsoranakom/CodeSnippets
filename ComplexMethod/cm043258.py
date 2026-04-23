def get_quality_confidence(self, state: CrawlState) -> float:
        """Calculate quality-based confidence score for display"""
        learning_score = state.metrics.get('learning_score', 0.0)
        validation_score = state.metrics.get('validation_confidence', 0.0)

        # Get config values
        validation_min = self.config.embedding_validation_min_score if hasattr(self, 'config') else 0.4
        quality_min = self.config.embedding_quality_min_confidence if hasattr(self, 'config') else 0.7
        quality_max = self.config.embedding_quality_max_confidence if hasattr(self, 'config') else 0.95
        scale_factor = self.config.embedding_quality_scale_factor if hasattr(self, 'config') else 0.833

        if self._validation_passed and validation_score > validation_min:
            # Validated systems get boosted scores
            # Map 0.4-0.7 learning → quality_min-quality_max confidence
            if learning_score < 0.4:
                confidence = quality_min  # Minimum for validated systems
            elif learning_score > 0.7:
                confidence = quality_max  # Maximum realistic confidence
            else:
                # Linear mapping in between
                confidence = quality_min + (learning_score - 0.4) * scale_factor
        else:
            # Not validated = conservative mapping
            confidence = learning_score * 0.8

        return confidence