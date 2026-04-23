def test_alter_index_together(self):
        """
        Tests the AlterIndexTogether operation.
        """
        project_state = self.set_up_test_model("test_alinto")
        # Test the state alteration
        operation = migrations.AlterIndexTogether("Pony", [("pink", "weight")])
        self.assertEqual(
            operation.describe(), "Alter index_together for Pony (1 constraint(s))"
        )
        self.assertEqual(
            operation.migration_name_fragment,
            "alter_pony_index_together",
        )
        new_state = project_state.clone()
        operation.state_forwards("test_alinto", new_state)
        self.assertEqual(
            len(
                project_state.models["test_alinto", "pony"].options.get(
                    "index_together", set()
                )
            ),
            0,
        )
        self.assertEqual(
            len(
                new_state.models["test_alinto", "pony"].options.get(
                    "index_together", set()
                )
            ),
            1,
        )
        # Make sure there's no matching index
        self.assertIndexNotExists("test_alinto_pony", ["pink", "weight"])
        # Test the database alteration
        with connection.schema_editor() as editor:
            operation.database_forwards("test_alinto", editor, project_state, new_state)
        self.assertIndexExists("test_alinto_pony", ["pink", "weight"])
        # And test reversal
        with connection.schema_editor() as editor:
            operation.database_backwards(
                "test_alinto", editor, new_state, project_state
            )
        self.assertIndexNotExists("test_alinto_pony", ["pink", "weight"])
        # And deconstruction
        definition = operation.deconstruct()
        self.assertEqual(definition[0], "AlterIndexTogether")
        self.assertEqual(definition[1], [])
        self.assertEqual(
            definition[2], {"name": "Pony", "index_together": {("pink", "weight")}}
        )