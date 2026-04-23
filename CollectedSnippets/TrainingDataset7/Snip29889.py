def test_drop_nonexistent_extension(self):
        operation = CreateExtension("tablefunc")
        project_state = ProjectState()
        new_state = project_state.clone()
        # Don't drop a nonexistent extension.
        with CaptureQueriesContext(connection) as captured_queries:
            with connection.schema_editor(atomic=False) as editor:
                operation.database_backwards(
                    self.app_label, editor, project_state, new_state
                )
        self.assertEqual(len(captured_queries), 1)
        self.assertIn("SELECT", captured_queries[0]["sql"])