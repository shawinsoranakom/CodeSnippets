def test_rename_index(self):
        app_label = "test_rnin"
        project_state = self.set_up_test_model(app_label, index=True)
        table_name = app_label + "_pony"
        self.assertIndexNameExists(table_name, "pony_pink_idx")
        self.assertIndexNameNotExists(table_name, "new_pony_test_idx")
        operation = migrations.RenameIndex(
            "Pony", new_name="new_pony_test_idx", old_name="pony_pink_idx"
        )
        self.assertEqual(
            operation.describe(),
            "Rename index pony_pink_idx on Pony to new_pony_test_idx",
        )
        self.assertEqual(
            operation.formatted_description(),
            "~ Rename index pony_pink_idx on Pony to new_pony_test_idx",
        )
        self.assertEqual(
            operation.migration_name_fragment,
            "rename_pony_pink_idx_new_pony_test_idx",
        )

        new_state = project_state.clone()
        operation.state_forwards(app_label, new_state)
        # Rename index.
        expected_queries = 1 if connection.features.can_rename_index else 2
        with (
            connection.schema_editor() as editor,
            self.assertNumQueries(expected_queries),
        ):
            operation.database_forwards(app_label, editor, project_state, new_state)
        self.assertIndexNameNotExists(table_name, "pony_pink_idx")
        self.assertIndexNameExists(table_name, "new_pony_test_idx")
        # Reversal.
        with (
            connection.schema_editor() as editor,
            self.assertNumQueries(expected_queries),
        ):
            operation.database_backwards(app_label, editor, new_state, project_state)
        self.assertIndexNameExists(table_name, "pony_pink_idx")
        self.assertIndexNameNotExists(table_name, "new_pony_test_idx")
        # Deconstruction.
        definition = operation.deconstruct()
        self.assertEqual(definition[0], "RenameIndex")
        self.assertEqual(definition[1], [])
        self.assertEqual(
            definition[2],
            {
                "model_name": "Pony",
                "old_name": "pony_pink_idx",
                "new_name": "new_pony_test_idx",
            },
        )