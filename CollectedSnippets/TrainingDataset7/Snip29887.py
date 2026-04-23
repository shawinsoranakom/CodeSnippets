def test_allow_migrate_based_on_hints(self):
        operation_no_hints = CreateExtension("tablefunc")
        self.assertEqual(operation_no_hints.hints, {})

        operation_hints = CreateExtension("tablefunc", hints={"a_hint": True})
        self.assertEqual(operation_hints.hints, {"a_hint": True})

        project_state = ProjectState()
        new_state = project_state.clone()

        with (
            CaptureQueriesContext(connection) as captured_queries,
            connection.schema_editor(atomic=False) as editor,
        ):
            operation_no_hints.database_forwards(
                self.app_label, editor, project_state, new_state
            )
        self.assertEqual(len(captured_queries), 0)

        with (
            CaptureQueriesContext(connection) as captured_queries,
            connection.schema_editor(atomic=False) as editor,
        ):
            operation_no_hints.database_backwards(
                self.app_label, editor, project_state, new_state
            )
        self.assertEqual(len(captured_queries), 0)

        with (
            CaptureQueriesContext(connection) as captured_queries,
            connection.schema_editor(atomic=False) as editor,
        ):
            operation_hints.database_forwards(
                self.app_label, editor, project_state, new_state
            )
        self.assertEqual(len(captured_queries), 4)
        self.assertIn("CREATE EXTENSION IF NOT EXISTS", captured_queries[1]["sql"])

        with (
            CaptureQueriesContext(connection) as captured_queries,
            connection.schema_editor(atomic=False) as editor,
        ):
            operation_hints.database_backwards(
                self.app_label, editor, project_state, new_state
            )
        self.assertEqual(len(captured_queries), 2)
        self.assertIn("DROP EXTENSION IF EXISTS", captured_queries[1]["sql"])