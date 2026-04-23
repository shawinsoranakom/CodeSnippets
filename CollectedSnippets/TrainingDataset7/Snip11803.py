def get_prep_lookup(self):
        from django.db.models.sql.query import Query  # avoid circular import

        if isinstance(query := self.rhs, Query):
            if not query.has_limit_one():
                raise ValueError(
                    "The QuerySet value for an exact lookup must be limited to "
                    "one result using slicing."
                )
            lhs_len = len(self.lhs) if isinstance(self.lhs, (ColPairs, tuple)) else 1
            if (rhs_len := query._subquery_fields_len) != lhs_len:
                raise ValueError(
                    f"The QuerySet value for the exact lookup must have {lhs_len} "
                    f"selected fields (received {rhs_len})"
                )
            if not query.has_select_fields:
                query.clear_select_clause()
                query.add_fields(["pk"])
        return super().get_prep_lookup()