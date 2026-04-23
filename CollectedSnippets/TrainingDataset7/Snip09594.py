def _set_field_new_type(self, field, new_type):
        """
        Keep the NULL and DEFAULT properties of the old field. If it has
        changed, it will be handled separately.
        """
        if field.has_db_default():
            default_sql, params = self.db_default_sql(field)
            default_sql %= tuple(self.quote_value(p) for p in params)
            new_type += f" DEFAULT {default_sql}"
        if field.null:
            new_type += " NULL"
        else:
            new_type += " NOT NULL"
        return new_type