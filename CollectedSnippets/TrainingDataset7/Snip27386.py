def test_alter_unique_together(self):
        """
        Tests the AlterUniqueTogether operation.
        """
        project_state = self.set_up_test_model("test_alunto")
        # Test the state alteration
        operation = migrations.AlterUniqueTogether("Pony", [("pink", "weight")])
        self.assertEqual(
            operation.describe(), "Alter unique_together for Pony (1 constraint(s))"
        )
        self.assertEqual(
            operation.formatted_description(),
            "~ Alter unique_together for Pony (1 constraint(s))",
        )
        self.assertEqual(
            operation.migration_name_fragment,
            "alter_pony_unique_together",
        )
        new_state = project_state.clone()
        operation.state_forwards("test_alunto", new_state)
        self.assertEqual(
            len(
                project_state.models["test_alunto", "pony"].options.get(
                    "unique_together", set()
                )
            ),
            0,
        )
        self.assertEqual(
            len(
                new_state.models["test_alunto", "pony"].options.get(
                    "unique_together", set()
                )
            ),
            1,
        )
        # Make sure we can insert duplicate rows
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO test_alunto_pony (pink, weight) VALUES (1, 1)")
            cursor.execute("INSERT INTO test_alunto_pony (pink, weight) VALUES (1, 1)")
            cursor.execute("DELETE FROM test_alunto_pony")
            # Test the database alteration
            with connection.schema_editor() as editor:
                operation.database_forwards(
                    "test_alunto", editor, project_state, new_state
                )
            cursor.execute("INSERT INTO test_alunto_pony (pink, weight) VALUES (1, 1)")
            with self.assertRaises(IntegrityError):
                with atomic():
                    cursor.execute(
                        "INSERT INTO test_alunto_pony (pink, weight) VALUES (1, 1)"
                    )
            cursor.execute("DELETE FROM test_alunto_pony")
            # And test reversal
            with connection.schema_editor() as editor:
                operation.database_backwards(
                    "test_alunto", editor, new_state, project_state
                )
            cursor.execute("INSERT INTO test_alunto_pony (pink, weight) VALUES (1, 1)")
            cursor.execute("INSERT INTO test_alunto_pony (pink, weight) VALUES (1, 1)")
            cursor.execute("DELETE FROM test_alunto_pony")
        # Test flat unique_together
        operation = migrations.AlterUniqueTogether("Pony", ("pink", "weight"))
        operation.state_forwards("test_alunto", new_state)
        self.assertEqual(
            len(
                new_state.models["test_alunto", "pony"].options.get(
                    "unique_together", set()
                )
            ),
            1,
        )
        # And deconstruction
        definition = operation.deconstruct()
        self.assertEqual(definition[0], "AlterUniqueTogether")
        self.assertEqual(definition[1], [])
        self.assertEqual(
            definition[2], {"name": "Pony", "unique_together": {("pink", "weight")}}
        )