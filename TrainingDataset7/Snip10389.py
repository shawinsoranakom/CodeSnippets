def database_forwards(self, app_label, schema_editor, from_state, to_state):
        # We calculate state separately in here since our state functions
        # aren't useful
        for database_operation in self.database_operations:
            to_state = from_state.clone()
            database_operation.state_forwards(app_label, to_state)
            database_operation.database_forwards(
                app_label, schema_editor, from_state, to_state
            )
            from_state = to_state