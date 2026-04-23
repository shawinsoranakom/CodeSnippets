def _column_default_sql(self, field):
        """
        Return the SQL to use in a DEFAULT clause. The resulting string should
        contain a '%s' placeholder for a default value.
        """
        return "%s"