def get_prep_lookup(self):
        from django.db.models.sql.query import Query  # avoid circular import

        if isinstance(self.rhs, Query):
            lhs_len = len(self.lhs) if isinstance(self.lhs, (ColPairs, tuple)) else 1
            if (rhs_len := self.rhs._subquery_fields_len) != lhs_len:
                raise ValueError(
                    f"The QuerySet value for the 'in' lookup must have {lhs_len} "
                    f"selected fields (received {rhs_len})"
                )
            self.rhs.clear_ordering(clear_default=True)
            if not self.rhs.has_select_fields:
                self.rhs.clear_select_clause()
                self.rhs.add_fields(["pk"])
        return super().get_prep_lookup()