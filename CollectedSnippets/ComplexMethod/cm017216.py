def alter_field(self, model, old_field, new_field, strict=False):
        try:
            super().alter_field(model, old_field, new_field, strict)
        except DatabaseError as e:
            description = str(e)
            # If we're changing type to an unsupported type we need a
            # SQLite-ish workaround
            if "ORA-22858" in description or "ORA-22859" in description:
                self._alter_field_type_workaround(model, old_field, new_field)
            # If an identity column is changing to a non-numeric type, drop the
            # identity first.
            elif "ORA-30675" in description:
                self._drop_identity(model._meta.db_table, old_field.column)
                self.alter_field(model, old_field, new_field, strict)
            # If a primary key column is changing to an identity column, drop
            # the primary key first.
            elif "ORA-30673" in description and old_field.primary_key:
                self._delete_primary_key(model, strict=True)
                self._alter_field_type_workaround(model, old_field, new_field)
            # If a collation is changing on a primary key, drop the primary key
            # first.
            elif "ORA-43923" in description and old_field.primary_key:
                self._delete_primary_key(model, strict=True)
                self.alter_field(model, old_field, new_field, strict)
                # Restore a primary key, if needed.
                if new_field.primary_key:
                    self.execute(self._create_primary_key_sql(model, new_field))
            else:
                raise