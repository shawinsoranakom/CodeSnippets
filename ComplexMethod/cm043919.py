def find_bop_group_prefix(
        self,
        target_order: int | float,
        target_title: str,
        displayed_orders: set[int | float] | None = None,
    ) -> str | None:
        """Find BOP-style group prefix for Credit/Debit/Net patterns.

        BOP tables have patterns like:
        - "Goods, Credit" (order 3.000)
        - "Goods, Debit" (order 3.001)
        - "Goods, Net" (order 3.002)

        These are all at the same level but form a logical group.
        When we see "Goods, Credit", we should strip "Goods, " because
        "Goods, Net" (which becomes "Goods" after Net stripping) serves
        as the implicit header for this group.

        Parameters
        ----------
        target_order : int | float
            The order value of the target row.
        target_title : str
            The title to find a group prefix for.
        displayed_orders : set[int | float] | None
            Set of order values that will actually be displayed.

        Returns
        -------
        str | None
            The group prefix to strip (e.g., "Goods, "), or None.
        """
        # BOP suffixes that indicate a grouped entry
        bop_suffixes = [", Credit", ", Debit", ", Net"]

        # Check if this title ends with a BOP suffix
        base_name = None
        our_suffix = None
        for suffix in bop_suffixes:
            if target_title.endswith(suffix):
                base_name = target_title[: -len(suffix)]
                our_suffix = suffix
                break

        if base_name is None:
            return None

        # For ", Net" suffix, don't strip - it becomes the group header
        if our_suffix == ", Net":
            return None

        # Find siblings with the same base name
        target_level = None
        for order, _, level, _ in self.order_title_level:
            if order == target_order:
                target_level = level
                break

        if target_level is None:
            return None

        # Get nearby siblings (within a small order range to find the group)
        siblings = self._get_true_siblings(target_order, target_level)

        # Filter to displayed siblings
        if displayed_orders is not None:
            siblings = [(o, t) for o, t in siblings if o in displayed_orders]

        # Check if there's a matching Net entry with the same base
        has_matching_net = False
        for _, sib_title in siblings:
            if sib_title == f"{base_name}, Net":
                has_matching_net = True
                break

        if has_matching_net:
            # Strip the base name + ", " prefix
            return f"{base_name}, "

        return None