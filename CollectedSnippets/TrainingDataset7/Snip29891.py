def test_create(self):
        operation = CreateCollation("C_test", locale="C")
        self.assertEqual(operation.migration_name_fragment, "create_collation_c_test")
        self.assertEqual(operation.describe(), "Create collation C_test")
        self.assertEqual(operation.formatted_description(), "+ Create collation C_test")
        project_state = ProjectState()
        new_state = project_state.clone()
        # Create a collation.
        with CaptureQueriesContext(connection) as captured_queries:
            with connection.schema_editor(atomic=False) as editor:
                operation.database_forwards(
                    self.app_label, editor, project_state, new_state
                )
        self.assertEqual(len(captured_queries), 1)
        self.assertIn("CREATE COLLATION", captured_queries[0]["sql"])
        # Creating the same collation raises an exception.
        with self.assertRaisesMessage(ProgrammingError, "already exists"):
            with connection.schema_editor(atomic=True) as editor:
                operation.database_forwards(
                    self.app_label, editor, project_state, new_state
                )
        # Reversal.
        with CaptureQueriesContext(connection) as captured_queries:
            with connection.schema_editor(atomic=False) as editor:
                operation.database_backwards(
                    self.app_label, editor, new_state, project_state
                )
        self.assertEqual(len(captured_queries), 1)
        self.assertIn("DROP COLLATION", captured_queries[0]["sql"])
        # Deconstruction.
        name, args, kwargs = operation.deconstruct()
        self.assertEqual(name, "CreateCollation")
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"name": "C_test", "locale": "C"})