def date_extract_sql(self, lookup_type, sql, params):
        """
        Support EXTRACT with a user-defined function django_date_extract()
        that's registered in connect(). Use single quotes because this is a
        string and could otherwise cause a collision with a field name.
        """
        return f"django_date_extract(%s, {sql})", (lookup_type.lower(), *params)