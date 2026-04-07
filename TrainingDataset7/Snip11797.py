def get_db_prep_lookup(self, value, connection):
        # For relational fields, use the 'target_field' attribute of the
        # output_field.
        field = getattr(self.lhs.output_field, "target_field", None)
        get_db_prep_value = (
            getattr(field, "get_db_prep_value", None)
            or self.lhs.output_field.get_db_prep_value
        )
        if not self.get_db_prep_lookup_value_is_iterable:
            value = [value]
        return (
            "%s",
            [
                (
                    v
                    if hasattr(v, "as_sql")
                    else get_db_prep_value(v, connection, prepared=True)
                )
                for v in value
            ],
        )