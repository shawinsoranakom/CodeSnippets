def new_format_sql(self, sql):
        # Use time() to introduce some uniqueness.
        formatted = "Formatted! %s at %s" % (sql.upper(), time())
        self.format_sql_calls.append({sql: formatted})
        return formatted