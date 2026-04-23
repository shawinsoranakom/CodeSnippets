def find_ancestor_part_prefix(
        self,
        target_order: int | float,
        target_title: str,
        displayed_orders: set[int | float] | None = None,
    ) -> str | None:
        """Find ancestor context parts that appear as a prefix in the title.

        Some IMF titles have ancestor context as a prefix:
        - Parent: "Liabilities"
        - Child: "Total liabilities, Domestic Creditors"

        The "Total liabilities, " prefix is redundant since parent is "Liabilities".

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
            The matching prefix (including trailing ", " or ": "), or None.
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

        levels_seen: set = set()
        ancestor_parts: set = set()

        for i in range(target_idx - 1, -1, -1):
            order, title, level, _ = self.order_title_level[i]
            if level < target_level:
                if level in levels_seen:
                    continue
                levels_seen.add(level)

                if displayed_orders is not None and order not in displayed_orders:
                    continue

                if not title:
                    continue

                if title == target_title:
                    continue

                parts = re.split(r", (?=[A-Z:])", title)

                for p in parts:
                    pp = p.strip()
                    if pp:
                        ancestor_parts.add(pp)
                        # Add related patterns
                        if pp == "Liabilities":
                            ancestor_parts.add("Total liabilities")
                        elif pp == "Financial assets":
                            ancestor_parts.add("Financial assets")

        if not ancestor_parts:
            return None

        # Check if title starts with "<ancestor_part>, " or "<ancestor_part>: "
        strippable_single_words = {"Assets", "Liabilities"}
        target_normalized = target_title.lower().replace("-", " ")
        for part in ancestor_parts:
            # Skip single-word parts unless they're known category markers
            if " " not in part and part not in strippable_single_words:
                continue
            part_normalized = part.lower().replace("-", " ")
            # Check both comma and colon separators
            for sep in [", ", ": "]:
                prefix_with_sep = f"{part}{sep}"
                if target_title.startswith(prefix_with_sep):
                    # SAFEGUARD: Don't return if remainder is just a BOP suffix
                    remainder = target_title[len(prefix_with_sep) :]
                    if is_bop_suffix_only(remainder):
                        continue
                    return prefix_with_sep
                # Also check normalized version
                prefix_normalized = f"{part_normalized}{sep}"
                if target_normalized.startswith(prefix_normalized):
                    # SAFEGUARD: Don't return if remainder is just a BOP suffix
                    remainder = target_title[len(prefix_normalized) :]
                    if is_bop_suffix_only(remainder):
                        continue
                    return target_title[: len(prefix_normalized)]

        # Check if title starts with a PARTIAL version of an ancestor part
        # e.g., Parent: "A to B liabilities", Child: "A to B , X"
        # The child prefix "A to B , " is a partial match of parent
        if ", " in target_title:
            comma_idx = target_title.index(", ")
            child_prefix = target_title[:comma_idx].lower().replace("-", " ")
            for part in ancestor_parts:
                part_normalized = part.lower().replace("-", " ")
                # Check if child prefix is a prefix of the ancestor part
                if part_normalized.startswith(child_prefix) and len(child_prefix) > 10:
                    # SAFEGUARD: Don't return if remainder is just a BOP suffix
                    remainder = target_title[comma_idx + 2 :]
                    if is_bop_suffix_only(remainder):
                        continue
                    # Strip the prefix plus ", "
                    return target_title[: comma_idx + 2]

        return None