def supports_explaining_query_execution(self):
        """Does this backend support explaining query execution?"""
        return self.connection.ops.explain_prefix is not None