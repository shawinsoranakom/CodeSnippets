def _score_image_candidate(col, sample_value):
        """Score a candidate image column by how resolvable its value is."""
        # PIL Image object (highest priority - already loaded)
        if hasattr(sample_value, "size") and hasattr(sample_value, "mode"):
            return 100

        # Dict with image data (bytes/path from HF Image feature)
        if isinstance(sample_value, dict) and (
            "bytes" in sample_value or "path" in sample_value
        ):
            return 75

        if isinstance(sample_value, str):
            # URL strings
            if sample_value.startswith(("http://", "https://")):
                return 70 if not is_metadata_column(col) else 55
            # Bare file path
            if is_metadata_column(col):
                return 30
            return 50

        return 0