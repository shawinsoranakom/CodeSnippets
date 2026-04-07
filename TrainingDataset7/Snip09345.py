def format_debug_sql(self, sql):
        # Hook for backends (e.g. NoSQL) to customize formatting.
        return sqlparse.format(sql, reindent=True, keyword_case="upper")