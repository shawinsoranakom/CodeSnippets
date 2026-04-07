def test_remove_field(self):
        """
        Tests the RemoveField operation.
        """
        project_state = self.set_up_test_model("test_rmfl")
        # Test the state alteration
        operation = migrations.RemoveField("Pony", "pink")
        self.assertEqual(operation.describe(), "Remove field pink from Pony")
        self.assertEqual(
            operation.formatted_description(), "- Remove field pink from Pony"
        )
        self.assertEqual(operation.migration_name_fragment, "remove_pony_pink")
        new_state = project_state.clone()
        operation.state_forwards("test_rmfl", new_state)
        self.assertEqual(len(new_state.models["test_rmfl", "pony"].fields), 4)
        # Test the database alteration
        self.assertColumnExists("test_rmfl_pony", "pink")
        with (
            connection.schema_editor() as editor,
            CaptureQueriesContext(connection) as ctx,
        ):
            operation.database_forwards("test_rmfl", editor, project_state, new_state)
        self.assertGreater(len(ctx.captured_queries), 0)
        self.assertNotIn("CASCADE", ctx.captured_queries[-1]["sql"])
        self.assertColumnNotExists("test_rmfl_pony", "pink")
        # And test reversal
        with connection.schema_editor() as editor:
            operation.database_backwards("test_rmfl", editor, new_state, project_state)
        self.assertColumnExists("test_rmfl_pony", "pink")
        # And deconstruction
        definition = operation.deconstruct()
        self.assertEqual(definition[0], "RemoveField")
        self.assertEqual(definition[1], [])
        self.assertEqual(definition[2], {"model_name": "Pony", "name": "pink"})