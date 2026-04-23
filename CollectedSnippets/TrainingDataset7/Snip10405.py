def database_backwards(self, app_label, schema_editor, from_state, to_state):
        if self.reverse_code is None:
            raise NotImplementedError("You cannot reverse this operation")
        if router.allow_migrate(
            schema_editor.connection.alias, app_label, **self.hints
        ):
            self.reverse_code(from_state.apps, schema_editor)