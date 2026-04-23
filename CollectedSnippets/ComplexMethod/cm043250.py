def validate(self):
        """Validate configuration parameters"""
        assert 0 <= self.confidence_threshold <= 1, "confidence_threshold must be between 0 and 1"
        assert self.max_depth > 0, "max_depth must be positive"
        assert self.max_pages > 0, "max_pages must be positive"
        assert self.top_k_links > 0, "top_k_links must be positive"
        assert 0 <= self.min_gain_threshold <= 1, "min_gain_threshold must be between 0 and 1"

        # Check weights sum to 1
        weight_sum = self.coverage_weight + self.consistency_weight + self.saturation_weight
        assert abs(weight_sum - 1.0) < 0.001, f"Coverage weights must sum to 1, got {weight_sum}"

        weight_sum = self.relevance_weight + self.novelty_weight + self.authority_weight
        assert abs(weight_sum - 1.0) < 0.001, f"Link scoring weights must sum to 1, got {weight_sum}"

        # Validate embedding parameters
        assert 0 < self.embedding_coverage_radius < 1, "embedding_coverage_radius must be between 0 and 1"
        assert self.embedding_k_exp > 0, "embedding_k_exp must be positive"
        assert 0 <= self.embedding_nearest_weight <= 1, "embedding_nearest_weight must be between 0 and 1"
        assert 0 <= self.embedding_top_k_weight <= 1, "embedding_top_k_weight must be between 0 and 1"
        assert abs(self.embedding_nearest_weight + self.embedding_top_k_weight - 1.0) < 0.001, "Embedding weights must sum to 1"
        assert 0 <= self.embedding_overlap_threshold <= 1, "embedding_overlap_threshold must be between 0 and 1"
        assert 0 < self.embedding_min_relative_improvement < 1, "embedding_min_relative_improvement must be between 0 and 1"
        assert 0 <= self.embedding_validation_min_score <= 1, "embedding_validation_min_score must be between 0 and 1"
        assert 0 <= self.embedding_quality_min_confidence <= 1, "embedding_quality_min_confidence must be between 0 and 1"
        assert 0 <= self.embedding_quality_max_confidence <= 1, "embedding_quality_max_confidence must be between 0 and 1"
        assert self.embedding_quality_scale_factor > 0, "embedding_quality_scale_factor must be positive"