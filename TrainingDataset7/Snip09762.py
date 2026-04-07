def _alter_column_type_sql(
        self, model, old_field, new_field, new_type, old_collation, new_collation
    ):
        auto_field_types = {"AutoField", "BigAutoField", "SmallAutoField"}
        # Drop the identity if migrating away from AutoField.
        if (
            old_field.get_internal_type() in auto_field_types
            and new_field.get_internal_type() not in auto_field_types
            and self._is_identity_column(model._meta.db_table, new_field.column)
        ):
            self._drop_identity(model._meta.db_table, new_field.column)
        return super()._alter_column_type_sql(
            model, old_field, new_field, new_type, old_collation, new_collation
        )