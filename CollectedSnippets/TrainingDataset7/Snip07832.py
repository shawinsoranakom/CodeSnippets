def database_backwards(self, app_label, schema_editor, from_state, to_state):
        # PostgreSQL does not provide a way to make a constraint invalid.
        pass