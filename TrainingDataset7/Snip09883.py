def execute(self, sql, params=()):
        # Merge the query client-side, as PostgreSQL won't do it server-side.
        if params is None:
            return super().execute(sql, params)
        sql = self.connection.ops.compose_sql(str(sql), params)
        # Don't let the superclass touch anything.
        return super().execute(sql, None)