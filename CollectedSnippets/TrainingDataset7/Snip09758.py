def remove_field(self, model, field):
        # If the column is an identity column, drop the identity before
        # removing the field.
        if self._is_identity_column(model._meta.db_table, field.column):
            self._drop_identity(model._meta.db_table, field.column)
        super().remove_field(model, field)