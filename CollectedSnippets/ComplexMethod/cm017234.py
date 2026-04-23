def _alter_field(
        self,
        model,
        old_field,
        new_field,
        old_type,
        new_type,
        old_db_params,
        new_db_params,
        strict=False,
    ):
        """Perform a "physical" (non-ManyToMany) field update."""
        # Use "ALTER TABLE ... RENAME COLUMN" if only the column name
        # changed and there aren't any constraints.
        if (
            old_field.column != new_field.column
            and self.column_sql(model, old_field) == self.column_sql(model, new_field)
            and not (
                old_field.remote_field
                and old_field.db_constraint
                or new_field.remote_field
                and new_field.db_constraint
            )
        ):
            return self.execute(
                self._rename_field_sql(
                    model._meta.db_table, old_field, new_field, new_type
                )
            )
        # Alter by remaking table
        self._remake_table(model, alter_fields=[(old_field, new_field)])
        # Rebuild tables with FKs pointing to this field.
        old_collation = old_db_params.get("collation")
        new_collation = new_db_params.get("collation")
        if new_field.unique and (
            old_type != new_type or old_collation != new_collation
        ):
            related_models = set()
            opts = new_field.model._meta
            for remote_field in opts.related_objects:
                # Ignore self-relationship since the table was already rebuilt.
                if remote_field.related_model == model:
                    continue
                if not remote_field.many_to_many:
                    if remote_field.field_name == new_field.name:
                        related_models.add(remote_field.related_model)
                elif new_field.primary_key and remote_field.through._meta.auto_created:
                    related_models.add(remote_field.through)
            if new_field.primary_key:
                for many_to_many in opts.many_to_many:
                    # Ignore self-relationship since the table was already
                    # rebuilt.
                    if many_to_many.related_model == model:
                        continue
                    if many_to_many.remote_field.through._meta.auto_created:
                        related_models.add(many_to_many.remote_field.through)
            for related_model in related_models:
                self._remake_table(related_model)