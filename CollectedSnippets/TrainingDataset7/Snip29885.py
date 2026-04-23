def test_no_allow_migrate(self):
        operation = CreateExtension("tablefunc")
        self.assertEqual(
            operation.formatted_description(), "+ Creates extension tablefunc"
        )
        project_state = ProjectState()
        new_state = project_state.clone()
        # Don't create an extension.
        with CaptureQueriesContext(connection) as captured_queries:
            with connection.schema_editor(atomic=False) as editor:
                operation.database_forwards(
                    self.app_label, editor, project_state, new_state
                )
        self.assertEqual(len(captured_queries), 0)
        # Reversal.
        with CaptureQueriesContext(connection) as captured_queries:
            with connection.schema_editor(atomic=False) as editor:
                operation.database_backwards(
                    self.app_label, editor, new_state, project_state
                )
        self.assertEqual(len(captured_queries), 0)