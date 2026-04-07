def generate_renamed_fields(self):
        """Generate RenameField operations."""
        for (
            rem_app_label,
            rem_model_name,
            rem_db_column,
            rem_field_name,
            app_label,
            model_name,
            field,
            field_name,
        ) in self.renamed_operations:
            # A db_column mismatch requires a prior noop AlterField for the
            # subsequent RenameField to be a noop on attempts at preserving the
            # old name.
            if rem_db_column != field.db_column:
                altered_field = field.clone()
                altered_field.name = rem_field_name
                self.add_operation(
                    app_label,
                    operations.AlterField(
                        model_name=model_name,
                        name=rem_field_name,
                        field=altered_field,
                    ),
                )
            self.add_operation(
                app_label,
                operations.RenameField(
                    model_name=model_name,
                    old_name=rem_field_name,
                    new_name=field_name,
                ),
            )
            self.old_field_keys.remove((rem_app_label, rem_model_name, rem_field_name))
            self.old_field_keys.add((app_label, model_name, field_name))