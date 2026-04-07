def test_last_executed_query_without_previous_query(self):
        """
        last_executed_query should not raise an exception even if no previous
        query has been run.
        """
        suffix = connection.features.bare_select_suffix
        with connection.cursor() as cursor:
            if connection.vendor == "oracle":
                cursor.statement = None
            # No previous query has been run.
            connection.ops.last_executed_query(cursor, "", ())
            # Previous query crashed.
            connection.ops.last_executed_query(cursor, "SELECT %s" + suffix, (1,))