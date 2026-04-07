def database_backwards(self, app_label, schema_editor, from_state, to_state):
        # We calculate state separately in here since our state functions
        # aren't useful
        to_states = {}
        for dbop in self.database_operations:
            to_states[dbop] = to_state
            to_state = to_state.clone()
            dbop.state_forwards(app_label, to_state)
        # to_state now has the states of all the database_operations applied
        # which is the from_state for the backwards migration of the last
        # operation.
        for database_operation in reversed(self.database_operations):
            from_state = to_state
            to_state = to_states[database_operation]
            database_operation.database_backwards(
                app_label, schema_editor, from_state, to_state
            )