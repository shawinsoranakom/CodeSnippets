def database_forwards(self, app_label, schema_editor, from_state, to_state):
        if schema_editor.connection.vendor != "postgresql" or not router.allow_migrate(
            schema_editor.connection.alias, app_label
        ):
            return
        self.remove_collation(schema_editor)