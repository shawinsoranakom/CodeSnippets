def execute(self, sql, params=None):
        with self.debug_sql(sql, params, use_last_executed_query=True):
            return super().execute(sql, params)