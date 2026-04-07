def exists(self, limit=True):
        q = self.clone()
        if not (q.distinct and q.is_sliced):
            if q.group_by is True:
                q.add_fields(
                    (f.attname for f in self.model._meta.concrete_fields), False
                )
                # Disable GROUP BY aliases to avoid orphaning references to the
                # SELECT clause which is about to be cleared.
                q.set_group_by(allow_aliases=False)
            q.clear_select_clause()
        if q.combined_queries and q.combinator == "union":
            q.combined_queries = tuple(
                combined_query.exists(limit=False)
                for combined_query in q.combined_queries
            )
        q.clear_ordering(force=True)
        if limit is True:
            q.set_limits(high=1)
        q.add_annotation(Value(1), "a")
        return q