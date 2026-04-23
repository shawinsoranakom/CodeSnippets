def simplify_title(
        self,
        order: int | float,
        title: str,
        displayed_orders: set[int | float] | None = None,
    ) -> str:
        """Apply all title simplifications (strip suffix, prefix, ancestor parts).

        Parameters
        ----------
        order : int | float
            The order value of the row.
        title : str
            The raw title to simplify.
        displayed_orders : set[int | float] | None
            Set of order values that will actually be displayed.

        Returns
        -------
        str
            The simplified title.
        """
        title = strip_title_suffix(title)
        original_title = title  # Save for safeguard
        was_bop_group_stripped = False  # Track if BOP group stripping happened

        # Only strip prefixes from ancestors that will be displayed
        best_prefix = self.find_best_prefix(order, title, displayed_orders)
        if best_prefix and title.startswith(best_prefix):
            relative = title[len(best_prefix) :].lstrip(", :")
            # Only replace if relative is not empty, and it's not identical
            if relative and title != best_prefix:
                title = relative

        # Check for common prefix among siblings at the same level
        sibling_prefix = self.find_sibling_common_prefix(order, title, displayed_orders)
        if sibling_prefix and title.startswith(sibling_prefix):
            remainder = title[len(sibling_prefix) :]
            if remainder:  # Only strip if something remains
                title = remainder

        # Check for BOP-style Credit/Debit/Net grouping pattern
        # This is INTENTIONAL stripping - we WANT "Credit"/"Debit" as children of "Net" header
        bop_prefix = self.find_bop_group_prefix(order, title, displayed_orders)
        if bop_prefix and title.startswith(bop_prefix):
            remainder = title[len(bop_prefix) :]
            if remainder:  # Only strip if something remains
                title = remainder
                was_bop_group_stripped = True  # Mark that this was intentional

        # Strip ancestor-part prefixes before suffix stripping
        while True:
            part_prefix = self.find_ancestor_part_prefix(order, title, displayed_orders)
            if part_prefix and title.startswith(part_prefix):
                title = title[len(part_prefix) :]
            else:
                break

        # Then strip redundant suffixes from parent context
        while True:
            best_suffix = self.find_best_suffix(order, title, displayed_orders)
            if best_suffix and title.endswith(best_suffix):
                title = title[: -len(best_suffix)]
            else:
                break

        # SAFEGUARD: Never reduce title to ONLY a BOP suffix term
        # UNLESS it was intentionally stripped by BOP group logic (Credit/Debit under Net header)
        if not was_bop_group_stripped:
            bop_only_terms = {
                "Net",
                "Credit",
                "Debit",
                "Credit/Revenue",
                "Debit/Expenditure",
                "Assets",
                "Liabilities",
                "Assets (excl. reserves)",
                "Liabilities (incl. net incurrence)",
            }
            stripped_title = title.strip()
            if stripped_title in bop_only_terms:
                # Restore the original title (before any stripping)
                title = original_title

        # SAFEGUARD: Never return an empty title - restore original if stripped to nothing
        if not title or not title.strip():
            title = original_title

        return title