def execute_sql(self, result_type):
        """
        Execute the specified update. Return the number of rows affected by
        the primary update query. The "primary update query" is the first
        non-empty query that is executed. Row counts for any subsequent,
        related queries are not available.
        """
        row_count = super().execute_sql(result_type)
        is_empty = row_count is None
        row_count = row_count or 0

        for query in self.query.get_related_updates():
            # If the result_type is NO_RESULTS then the aux_row_count is None.
            aux_row_count = query.get_compiler(self.using).execute_sql(result_type)
            if is_empty and aux_row_count:
                # Returns the row count for any related updates as the number
                # of rows updated.
                row_count = aux_row_count
                is_empty = False
        return row_count