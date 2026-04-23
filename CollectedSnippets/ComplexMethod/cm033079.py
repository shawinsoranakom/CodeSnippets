def get_aggregation(self, res: tuple[pd.DataFrame, int] | pd.DataFrame, field_name: str):
        """
        Manual aggregation for tag fields since Infinity doesn't provide native aggregation
        """
        from collections import Counter

        # Extract DataFrame from result
        if isinstance(res, tuple):
            df, _ = res
        else:
            df = res

        if df.empty or field_name not in df.columns:
            return []

        # Aggregate tag counts
        tag_counter = Counter()

        for value in df[field_name]:
            if pd.isna(value) or not value:
                continue

            # Handle different tag formats
            if isinstance(value, str):
                # Split by ### for tag_kwd field or comma for other formats
                if field_name == "tag_kwd" and "###" in value:
                    tags = [tag.strip() for tag in value.split("###") if tag.strip()]
                else:
                    # Try comma separation as fallback
                    tags = [tag.strip() for tag in value.split(",") if tag.strip()]

                for tag in tags:
                    if tag:  # Only count non-empty tags
                        tag_counter[tag] += 1
            elif isinstance(value, list):
                # Handle list format
                for tag in value:
                    if tag and isinstance(tag, str):
                        tag_counter[tag.strip()] += 1

        # Return as list of [tag, count] pairs, sorted by count descending
        return [[tag, count] for tag, count in tag_counter.most_common()]