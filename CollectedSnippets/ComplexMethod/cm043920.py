def find_best_prefix(
        self,
        target_order: int | float,
        target_title: str,
        displayed_orders: set[int | float] | None = None,
    ) -> str | None:
        """Find the longest ancestor title that is a prefix of target_title.

        Parameters
        ----------
        target_order : int | float
            The order value of the target row.
        target_title : str
            The title to find a prefix for.
        displayed_orders : set[int | float] | None
            Set of order values that will actually be displayed.
            If provided, only consider ancestors in this set.

        Returns
        -------
        str | None
            The longest matching prefix, or None if no match found.
        """
        # Find this order in the sorted list
        target_idx = None
        target_level = 0
        for i, (order, title, level, _) in enumerate(self.order_title_level):
            if order == target_order:
                target_idx = i
                target_level = level
                break

        if target_idx is None:
            return None

        # Look backwards for ancestors
        best_prefix = None
        levels_seen: set = set()
        ancestor_key_phrases: set = set()

        for i in range(target_idx - 1, -1, -1):
            order, title, level, _ = self.order_title_level[i]
            # Only consider rows at lower levels
            if level < target_level:
                if level in levels_seen:
                    continue
                levels_seen.add(level)

                # If displayed_orders provided, only consider ancestors that will be shown
                if displayed_orders is not None and order not in displayed_orders:
                    continue

                if not title:
                    continue

                if target_title.startswith(title) and (
                    best_prefix is None or len(title) > len(best_prefix)
                ):
                    best_prefix = title

                title_lower = title.lower()

                if title_lower.endswith(")"):
                    paren_start = title_lower.rfind(" (")
                    if paren_start > 0:
                        title_lower = title_lower[:paren_start]

                # Remove common suffixes to get the key entity
                for suffix in [
                    " survey",
                    " (domestic currency, millions)",
                    " (percent of gdp)",
                ]:
                    if title_lower.endswith(suffix):
                        title_lower = title_lower[: -len(suffix)]
                # Store the normalized phrase
                if title_lower:
                    ancestor_key_phrases.add(title_lower.strip())

        # If no exact prefix match, check for key phrase matches
        if best_prefix is None and ancestor_key_phrases:
            target_lower = target_title.lower()
            # Normalize hyphens to spaces for matching
            target_normalized = target_lower.replace("-", " ")
            for phrase in sorted(ancestor_key_phrases, key=len, reverse=True):
                phrase_normalized = phrase.replace("-", " ")
                # Check if target starts with the phrase followed by ", " or ": "
                for sep in [", ", ": ", " - "]:
                    prefix_pattern = f"{phrase_normalized}{sep}"
                    if target_normalized.startswith(prefix_pattern):
                        # Find the actual case-preserved prefix in the original title
                        prefix_len = len(prefix_pattern)
                        best_prefix = target_title[:prefix_len]
                        break
                if best_prefix:
                    break

        # SAFEGUARD: Don't return prefix if it would leave only a BOP suffix
        # This prevents "Financial account balance..., Net (...)" from becoming just "Net (...)"
        if best_prefix:
            remainder = target_title[len(best_prefix) :].lstrip(", :")
            if is_bop_suffix_only(remainder):
                return None

        return best_prefix