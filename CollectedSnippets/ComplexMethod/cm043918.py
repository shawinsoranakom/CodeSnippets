def find_sibling_common_prefix(
        self,
        target_order: int | float,
        target_title: str,
        displayed_orders: set[int | float] | None = None,
    ) -> str | None:
        """Find common prefix shared by siblings at the same level.

        When multiple rows at the same level share a common prefix like
        "Depository corporations, Liabilities, ", this prefix is redundant
        and can be stripped to show cleaner titles.

        Only considers prefixes that end with ", " to avoid partial word matches.
        Requires at least 3 siblings sharing the prefix to consider it redundant.

        Parameters
        ----------
        target_order : int | float
            The order value of the target row.
        target_title : str
            The title to find a common prefix for.
        displayed_orders : set[int | float] | None
            Set of order values that will actually be displayed.

        Returns
        -------
        str | None
            The common prefix including trailing ", " to strip, or None.
        """
        # Find target's level
        target_level = None
        for order, _, level, _ in self.order_title_level:
            if order == target_order:
                target_level = level
                break

        if target_level is None:
            return None

        # Get true siblings (respecting parent boundaries)
        siblings = self._get_true_siblings(target_order, target_level)
        if len(siblings) < 3:
            return None

        # Filter to displayed siblings only
        if displayed_orders is not None:
            siblings = [(o, t) for o, t in siblings if o in displayed_orders]
            if len(siblings) < 3:
                return None

        # Split titles by ", " but preserve pattern for later reconstruction
        def get_prefix_segments(title: str) -> list[str]:
            """Split title into prefix segments (each ending with ', ')."""
            segments = []
            parts = re.split(r"(, )", title)
            current = ""
            for _, part in enumerate(parts):
                current += part
                if part == ", ":
                    segments.append(current)
                    current = ""
            return segments

        # Get segments for all sibling titles
        sibling_titles = [t for _, t in siblings if t]
        if len(sibling_titles) < 3:
            return None

        # Find the longest common prefix segments
        all_segments = [get_prefix_segments(t) for t in sibling_titles]
        if not all_segments:
            return None

        # Find how many prefix segments are shared by siblings
        min_segments = min(len(s) for s in all_segments)
        common_count = 0
        for i in range(min_segments):
            first_seg = all_segments[0][i].lower()
            if all(segs[i].lower() == first_seg for segs in all_segments):
                common_count += 1
            else:
                break

        if common_count == 0:
            return None

        # Build the common prefix string
        common_prefix = "".join(all_segments[0][:common_count])

        # Make sure the target title starts with this prefix
        if not target_title.lower().startswith(common_prefix.lower()):
            return None

        # SAFEGUARD: Don't strip common prefix if ALL siblings end with BOP suffixes
        # (Credit/Debit/Net, Credit/Revenue, Debit/Expenditure, Assets, Liabilities)
        # In this case the common prefix IS the meaningful category name
        bop_endings = (
            ", Credit",
            ", Debit",
            ", Net",
            ", Credit/Revenue",
            ", Debit/Expenditure",
            ", Assets",
            ", Liabilities",
            " Assets",
            " Liabilities",
        )
        if all(
            any(t.endswith(ending) for ending in bop_endings) for t in sibling_titles
        ):
            return None

        # Return the actual prefix from the target (preserve case)
        return target_title[: len(common_prefix)]