def find_best_suffix(
        self,
        target_order: int | float,
        target_title: str,
        displayed_orders: set[int | float] | None = None,
    ) -> str | None:
        """Find ancestor context that appears as a suffix in the title.

        Many IMF tables have titles like:
        - Parent: "Domestic Creditors, Liabilities"
        - Child: "Currency and deposits, Net incurrence of liabilities, Domestic Creditors"

        The ", Domestic Creditors" suffix is redundant since it's shown in the parent.
        This function finds such suffixes to strip.

        Parameters
        ----------
        target_order : int | float
            The order value of the target row.
        target_title : str
            The title to find a suffix for.
        displayed_orders : set[int | float] | None
            Set of order values that will actually be displayed.
            If provided, only consider ancestors in this set.

        Returns
        -------
        str | None
            The matching suffix (including leading ", "), or None if no match.
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

        # Collect ALL suffix parts from ALL ancestors that we should strip
        # Start with immediate parent, go up the hierarchy
        levels_seen: set = set()
        ancestor_parts: set = set()
        # Never strip accounting-entry qualifiers like Net/Credit/Debit.
        # In BOP tables these are meaningful and required to preserve hierarchy.
        protected_suffixes = {
            "Assets",
            "Liabilities",
            "Net",
            "Credit",
            "Debit",
            "Credit/Revenue",
            "Debit/Expenditure",
        }

        for i in range(target_idx - 1, -1, -1):
            order, title, level, _ = self.order_title_level[i]
            if level < target_level:
                if level in levels_seen:
                    continue
                levels_seen.add(level)

                # If displayed_orders provided, only consider ancestors that will be shown
                if displayed_orders is not None and order not in displayed_orders:
                    continue

                if not title:
                    continue

                # Split on ", " followed by uppercase letter or colon hierarchy separator
                parts = re.split(r", (?=[A-Z:])", title)
                for p in parts:
                    pp = p.strip()
                    if pp:
                        ancestor_parts.add(pp)
                        # Also add related context patterns that imply each other
                        if pp == "Liabilities":
                            ancestor_parts.add("Net incurrence of liabilities")
                            ancestor_parts.add("Total liabilities")
                        elif pp == "Net acquisition of financial assets":
                            ancestor_parts.add("Net acquisition of financial assets")
                        elif pp == "Financial assets":
                            ancestor_parts.add("Assets")
                        elif "Debtors" in pp:
                            ancestor_parts.add("Net acquisition of financial assets")
                            ancestor_parts.add("Assets")
                        elif "Creditors" in pp:
                            ancestor_parts.add("Net incurrence of liabilities")
                            ancestor_parts.add("Total liabilities")

        # Try to find the rightmost comma-separated part that matches
        if not ancestor_parts:
            return None

        # Check if the title ends with ", <ancestor_part>"
        for part in ancestor_parts:
            if part in protected_suffixes:
                continue
            suffix_with_comma = f", {part}"
            if target_title.endswith(suffix_with_comma):
                return suffix_with_comma

        return None