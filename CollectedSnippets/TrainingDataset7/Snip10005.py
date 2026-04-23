def time_extract_sql(self, lookup_type, sql, params):
        return f"django_time_extract(%s, {sql})", (lookup_type.lower(), *params)