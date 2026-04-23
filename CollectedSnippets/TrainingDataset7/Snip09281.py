def distinct_sql(self, fields, params):
        """
        Return an SQL DISTINCT clause which removes duplicate rows from the
        result set. If any fields are given, only check the given fields for
        duplicates.
        """
        if fields:
            raise NotSupportedError(
                "DISTINCT ON fields is not supported by this database backend"
            )
        else:
            return ["DISTINCT"], []