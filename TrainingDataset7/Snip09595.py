def _alter_column_type_sql(
        self, model, old_field, new_field, new_type, old_collation, new_collation
    ):
        new_type = self._set_field_new_type(old_field, new_type)
        return super()._alter_column_type_sql(
            model, old_field, new_field, new_type, old_collation, new_collation
        )