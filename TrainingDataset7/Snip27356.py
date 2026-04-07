def test_alter_field(self):
        """
        Tests the AlterField operation.
        """
        project_state = self.set_up_test_model("test_alfl")
        # Test the state alteration
        operation = migrations.AlterField(
            "Pony", "pink", models.IntegerField(null=True)
        )
        self.assertEqual(operation.describe(), "Alter field pink on Pony")
        self.assertEqual(
            operation.formatted_description(), "~ Alter field pink on Pony"
        )
        self.assertEqual(operation.migration_name_fragment, "alter_pony_pink")
        new_state = project_state.clone()
        operation.state_forwards("test_alfl", new_state)
        self.assertIs(
            project_state.models["test_alfl", "pony"].fields["pink"].null, False
        )
        self.assertIs(new_state.models["test_alfl", "pony"].fields["pink"].null, True)
        # Test the database alteration
        self.assertColumnNotNull("test_alfl_pony", "pink")
        with connection.schema_editor() as editor:
            operation.database_forwards("test_alfl", editor, project_state, new_state)
        self.assertColumnNull("test_alfl_pony", "pink")
        # And test reversal
        with connection.schema_editor() as editor:
            operation.database_backwards("test_alfl", editor, new_state, project_state)
        self.assertColumnNotNull("test_alfl_pony", "pink")
        # And deconstruction
        definition = operation.deconstruct()
        self.assertEqual(definition[0], "AlterField")
        self.assertEqual(definition[1], [])
        self.assertEqual(sorted(definition[2]), ["field", "model_name", "name"])