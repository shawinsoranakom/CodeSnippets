def database_forwards(self, app_label, schema_editor, from_state, to_state):
        new_model = to_state.apps.get_model(app_label, self.name)
        if self.allow_migrate_model(schema_editor.connection.alias, new_model):
            old_model = from_state.apps.get_model(app_label, self.name)
            schema_editor.alter_db_table(
                new_model,
                old_model._meta.db_table,
                new_model._meta.db_table,
            )
            # Rename M2M fields whose name is based on this model's db_table
            for old_field, new_field in zip(
                old_model._meta.local_many_to_many, new_model._meta.local_many_to_many
            ):
                if new_field.remote_field.through._meta.auto_created:
                    schema_editor.alter_db_table(
                        new_field.remote_field.through,
                        old_field.remote_field.through._meta.db_table,
                        new_field.remote_field.through._meta.db_table,
                    )