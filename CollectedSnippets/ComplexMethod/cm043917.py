def _get_true_siblings(
        self, target_order: int | float, target_level: int
    ) -> list[tuple[int | float, str]]:
        """Get siblings that share the same parent (consecutive rows at same level).

        Siblings are rows at the same level that appear between parent boundaries.
        A parent boundary is any row at a lower level (parent) or a row at same
        level after a gap (different parent group).
        """
        # Find target index
        target_idx = None
        for i, (order, _, level, _) in enumerate(self.order_title_level):
            if order == target_order:
                target_idx = i
                break

        if target_idx is None:
            return []

        siblings: list[tuple[int | float, str]] = []

        # Look backwards to find start of sibling group (stop at parent or start)
        start_idx = target_idx
        for i in range(target_idx - 1, -1, -1):
            _, _, level, _ = self.order_title_level[i]
            if level < target_level:
                # Found parent, siblings start after this
                break
            if level == target_level:
                start_idx = i
            # Skip higher levels (children of previous siblings)

        # Look forwards to find end of sibling group (stop at parent or end)
        end_idx = target_idx
        for i in range(target_idx + 1, len(self.order_title_level)):
            _, _, level, _ = self.order_title_level[i]
            if level < target_level:
                # Found next parent, siblings end before this
                break
            if level == target_level:
                end_idx = i
            # Skip higher levels (children of siblings)

        # Collect all siblings (rows at target_level between start and end)
        for i in range(start_idx, end_idx + 1):
            order, title, level, _ = self.order_title_level[i]
            if level == target_level:
                siblings.append((order, title))

        return siblings