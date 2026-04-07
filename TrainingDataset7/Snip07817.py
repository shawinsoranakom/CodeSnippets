def database_backwards(self, app_label, schema_editor, from_state, to_state):
        if not router.allow_migrate(schema_editor.connection.alias, app_label):
            return
        self.remove_collation(schema_editor)