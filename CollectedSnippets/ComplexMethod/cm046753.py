def find_text_column():
        """Find text column by filtering out metadata and checking keywords."""
        candidates = []

        for col in column_names:
            # Skip metadata columns
            if is_metadata_column(col):
                continue

            # Check if contains text keywords (word-boundary match)
            if any(_keyword_in_column(keyword, col) for keyword in text_keywords):
                # Verify it's actually text
                sample_value = sample[col]

                if isinstance(sample_value, str) and len(sample_value) > 0:
                    # Longer text = higher priority (likely content, not just a label)
                    priority = min(len(sample_value), 1000)  # Cap at 1000
                    candidates.append((col, priority))
                elif (
                    isinstance(sample_value, list)
                    and len(sample_value) > 0
                    and isinstance(sample_value[0], str)
                ):
                    # List of strings (e.g. captions list) — lower priority than plain strings
                    priority = min(len(sample_value[0]), 1000) // 2
                    candidates.append((col, priority))

        # Return highest priority candidate
        if candidates:
            candidates.sort(key = lambda x: x[1], reverse = True)
            return candidates[0][0]

        return None