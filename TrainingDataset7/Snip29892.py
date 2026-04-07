def test_create_non_deterministic_collation(self):
        operation = CreateCollation(
            "case_insensitive_test",
            "und-u-ks-level2",
            provider="icu",
            deterministic=False,
        )
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
        self.assertEqual(
            kwargs,
            {
                "name": "case_insensitive_test",
                "locale": "und-u-ks-level2",
                "provider": "icu",
                "deterministic": False,
            },
        )