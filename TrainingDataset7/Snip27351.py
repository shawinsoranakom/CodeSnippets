def test_alter_model_table(self):
        """
        Tests the AlterModelTable operation.
        """
        project_state = self.set_up_test_model("test_almota")
        # Test the state alteration
        operation = migrations.AlterModelTable("Pony", "test_almota_pony_2")
        self.assertEqual(
            operation.describe(), "Rename table for Pony to test_almota_pony_2"
        )
        self.assertEqual(
            operation.formatted_description(),
            "~ Rename table for Pony to test_almota_pony_2",
        )
        self.assertEqual(operation.migration_name_fragment, "alter_pony_table")
        new_state = project_state.clone()
        operation.state_forwards("test_almota", new_state)
        self.assertEqual(
            new_state.models["test_almota", "pony"].options["db_table"],
            "test_almota_pony_2",
        )
        # Test the database alteration
        self.assertTableExists("test_almota_pony")
        self.assertTableNotExists("test_almota_pony_2")
        with connection.schema_editor() as editor:
            operation.database_forwards("test_almota", editor, project_state, new_state)
        self.assertTableNotExists("test_almota_pony")
        self.assertTableExists("test_almota_pony_2")
        # And test reversal
        with connection.schema_editor() as editor:
            operation.database_backwards(
                "test_almota", editor, new_state, project_state
            )
        self.assertTableExists("test_almota_pony")
        self.assertTableNotExists("test_almota_pony_2")
        # And deconstruction
        definition = operation.deconstruct()
        self.assertEqual(definition[0], "AlterModelTable")
        self.assertEqual(definition[1], [])
        self.assertEqual(definition[2], {"name": "Pony", "table": "test_almota_pony_2"})