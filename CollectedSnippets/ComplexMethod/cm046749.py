def is_metadata(col_name):
        """Check if column is likely metadata."""
        col_lower = col_name.lower()

        if col_lower in metadata_exact_match:
            return True

        if col_lower in metadata_prefix_patterns:
            return True

        for pattern in metadata_prefix_patterns:
            if (
                col_lower.startswith(pattern.split("_")[0] + "_")
                and col_lower != pattern
            ):
                if "_" in col_lower:
                    prefix = col_lower.split("_")[0]
                    if prefix in ["generation", "pass", "inference"]:
                        return True

        if len(col_lower) <= 2 and not col_lower in ["qa", "q", "a"]:
            return True

        return False