def get_db_prep_save(self, value, connection):
        # This slightly involved logic is to allow for `None` to be used to
        # store SQL `NULL` while `Value(None, JSONField())` can be used to
        # store JSON `null` while preventing compilable `as_sql` values from
        # making their way to `get_db_prep_value`, which is what the `super()`
        # implementation does.
        if value is None:
            return value
        if (
            isinstance(value, expressions.Value)
            and value.value is None
            and isinstance(value.output_field, JSONField)
        ):
            value = None
        return super().get_db_prep_save(value, connection)