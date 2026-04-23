def orderby_issubset_groupby(self):
        if self.extra_order_by:
            # Raw SQL from extra(order_by=...) can't be reliably compared
            # against resolved OrderBy/Col expressions. Treat as not a subset.
            return False
        if self.group_by in (None, True):
            # There is either no aggregation at all (None), or the group by
            # is generated automatically from model fields (True), in which
            # case the order by is necessarily a subset of them.
            return True
        if not self.order_by:
            # Although an empty set is always a subset, there's no point in
            # clearing ordering when there isn't any. Avoid the clone() below.
            return True
        # Don't pollute the original query (might disrupt joins).
        q = self.clone()
        order_by_set = {
            (
                order_by.resolve_expression(q)
                if hasattr(order_by, "resolve_expression")
                else F(order_by).resolve_expression(q)
            )
            for order_by in q.order_by
        }
        return order_by_set.issubset(self.group_by)