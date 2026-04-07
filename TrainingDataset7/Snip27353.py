def test_alter_model_table_noop(self):
        """
        Tests the AlterModelTable operation if the table name is not changed.
        """
        project_state = self.set_up_test_model("test_almota")
        # Test the state alteration
        operation = migrations.AlterModelTable("Pony", "test_almota_pony")
        new_state = project_state.clone()
        operation.state_forwards("test_almota", new_state)
        self.assertEqual(
            new_state.models["test_almota", "pony"].options["db_table"],
            "test_almota_pony",
        )
        # Test the database alteration
        self.assertTableExists("test_almota_pony")
        with connection.schema_editor() as editor:
            operation.database_forwards("test_almota", editor, project_state, new_state)
        self.assertTableExists("test_almota_pony")
        # And test reversal
        with connection.schema_editor() as editor:
            operation.database_backwards(
                "test_almota", editor, new_state, project_state
            )
        self.assertTableExists("test_almota_pony")