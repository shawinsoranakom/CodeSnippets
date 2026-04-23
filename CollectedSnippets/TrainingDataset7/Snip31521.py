def has_for_update_sql(self, queries, **kwargs):
        # Examine the SQL that was executed to determine whether it
        # contains the 'SELECT..FOR UPDATE' stanza.
        for_update_sql = connection.ops.for_update_sql(**kwargs)
        return any(for_update_sql in query["sql"] for query in queries)