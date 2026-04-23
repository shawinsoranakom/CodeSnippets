def test_separate_database_and_state(self):
        """
        Tests the SeparateDatabaseAndState operation.
        """
        project_state = self.set_up_test_model("test_separatedatabaseandstate")
        # Create the operation
        database_operation = migrations.RunSQL(
            "CREATE TABLE i_love_ponies (id int, special_thing int);",
            "DROP TABLE i_love_ponies;",
        )
        state_operation = migrations.CreateModel(
            "SomethingElse", [("id", models.AutoField(primary_key=True))]
        )
        operation = migrations.SeparateDatabaseAndState(
            state_operations=[state_operation], database_operations=[database_operation]
        )
        self.assertEqual(
            operation.describe(), "Custom state/database change combination"
        )
        self.assertEqual(
            operation.formatted_description(),
            "? Custom state/database change combination",
        )
        # Test the state alteration
        new_state = project_state.clone()
        operation.state_forwards("test_separatedatabaseandstate", new_state)
        self.assertEqual(
            len(
                new_state.models[
                    "test_separatedatabaseandstate", "somethingelse"
                ].fields
            ),
            1,
        )
        # Make sure there's no table
        self.assertTableNotExists("i_love_ponies")
        # Test the database alteration
        with connection.schema_editor() as editor:
            operation.database_forwards(
                "test_separatedatabaseandstate", editor, project_state, new_state
            )
        self.assertTableExists("i_love_ponies")
        # And test reversal
        self.assertTrue(operation.reversible)
        with connection.schema_editor() as editor:
            operation.database_backwards(
                "test_separatedatabaseandstate", editor, new_state, project_state
            )
        self.assertTableNotExists("i_love_ponies")
        # And deconstruction
        definition = operation.deconstruct()
        self.assertEqual(definition[0], "SeparateDatabaseAndState")
        self.assertEqual(definition[1], [])
        self.assertEqual(
            sorted(definition[2]), ["database_operations", "state_operations"]
        )