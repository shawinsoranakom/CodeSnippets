def alter_field(self, model, old_field, new_field, strict=False):
        """
        Allow a field's type, uniqueness, nullability, default, column,
        constraints, etc. to be modified.
        `old_field` is required to compute the necessary changes.
        If `strict` is True, raise errors if the old column does not match
        `old_field` precisely.
        """
        if not self._field_should_be_altered(old_field, new_field):
            return
        # Ensure this field is even column-based
        old_db_params = old_field.db_parameters(connection=self.connection)
        old_type = old_db_params["type"]
        new_db_params = new_field.db_parameters(connection=self.connection)
        new_type = new_db_params["type"]
        modifying_generated_field = False
        if (old_type is None and old_field.remote_field is None) or (
            new_type is None and new_field.remote_field is None
        ):
            raise ValueError(
                "Cannot alter field %s into %s - they do not properly define "
                "db_type (are you using a badly-written custom field?)"
                % (old_field, new_field),
            )
        elif (
            old_type is None
            and new_type is None
            and (
                old_field.remote_field.through
                and new_field.remote_field.through
                and old_field.remote_field.through._meta.auto_created
                and new_field.remote_field.through._meta.auto_created
            )
        ):
            return self._alter_many_to_many(model, old_field, new_field, strict)
        elif (
            old_type is None
            and new_type is None
            and (
                old_field.remote_field.through
                and new_field.remote_field.through
                and not old_field.remote_field.through._meta.auto_created
                and not new_field.remote_field.through._meta.auto_created
            )
        ):
            # Both sides have through models; this is a no-op.
            return
        elif old_type is None or new_type is None:
            raise ValueError(
                "Cannot alter field %s into %s - they are not compatible types "
                "(you cannot alter to or from M2M fields, or add or remove "
                "through= on M2M fields)" % (old_field, new_field)
            )
        elif old_field.generated != new_field.generated or (
            new_field.generated and old_field.db_persist != new_field.db_persist
        ):
            modifying_generated_field = True
        elif new_field.generated:
            try:
                old_field_sql = old_field.generated_sql(self.connection)
            except FieldError:
                # Field used in a generated field was renamed.
                modifying_generated_field = True
            else:
                new_field_sql = new_field.generated_sql(self.connection)
                modifying_generated_field = old_field_sql != new_field_sql
                db_features = self.connection.features
                # Some databases (e.g. Oracle) don't allow altering a data type
                # for generated columns.
                if (
                    not modifying_generated_field
                    and old_type != new_type
                    and not db_features.supports_alter_generated_column_data_type
                ):
                    modifying_generated_field = True
        if modifying_generated_field:
            raise ValueError(
                f"Modifying GeneratedFields is not supported - the field {new_field} "
                "must be removed and re-added with the new definition."
            )

        self._alter_field(
            model,
            old_field,
            new_field,
            old_type,
            new_type,
            old_db_params,
            new_db_params,
            strict,
        )