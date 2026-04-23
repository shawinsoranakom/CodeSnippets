def find_image_column():
        """Find image column by keyword match + value-based fallback.
        When multiple candidates exist, probes them to find one that works."""
        candidates = []

        # Pass 1: keyword-matched columns
        for col in column_names:
            if any(_keyword_in_column(keyword, col) for keyword in image_keywords):
                sample_value = sample[col]
                score = _score_image_candidate(col, sample_value)
                if score > 0:
                    candidates.append((col, score))

        # Pass 2: value-based fallback — find columns with image URLs/paths
        # even if the column name doesn't match image keywords
        already = {c[0] for c in candidates}
        for col in column_names:
            if col in already:
                continue
            sample_value = sample[col]
            if _is_image_value(sample_value):
                score = _score_image_candidate(col, sample_value)
                # Slightly penalise non-keyword columns so keyword matches win on ties
                candidates.append((col, max(score - 5, 1)))

        if not candidates:
            return None

        candidates.sort(key = lambda x: x[1], reverse = True)

        # Single candidate or top candidate is PIL/dict — no probing needed
        if len(candidates) == 1 or candidates[0][1] >= 75:
            return candidates[0][0]

        # Multiple string-based candidates — probe to find one that actually works
        for col, score in candidates:
            sample_value = sample[col]
            if _probe_image_candidate(col, sample_value):
                return col

        # Nothing probed successfully — return highest-scored anyway and let
        # conversion handle the error (it may still resolve via hf_hub_download)
        return candidates[0][0]