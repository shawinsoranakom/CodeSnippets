def test_rename_field_unique_together(self):
        project_state = self.set_up_test_model("test_rnflut", unique_together=True)
        operation = migrations.RenameField("Pony", "pink", "blue")
        new_state = project_state.clone()
        operation.state_forwards("test_rnflut", new_state)
        # unique_together has the renamed column.
        self.assertIn(
            "blue",
            list(new_state.models["test_rnflut", "pony"].options["unique_together"])[0],
        )
        self.assertNotIn(
            "pink",
            list(new_state.models["test_rnflut", "pony"].options["unique_together"])[0],
        )
        # Rename field.
        self.assertColumnExists("test_rnflut_pony", "pink")
        self.assertColumnNotExists("test_rnflut_pony", "blue")
        with connection.schema_editor() as editor:
            operation.database_forwards("test_rnflut", editor, project_state, new_state)
        self.assertColumnExists("test_rnflut_pony", "blue")
        self.assertColumnNotExists("test_rnflut_pony", "pink")
        # The unique constraint has been ported over.
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO test_rnflut_pony (blue, weight) VALUES (1, 1)")
            with self.assertRaises(IntegrityError):
                with atomic():
                    cursor.execute(
                        "INSERT INTO test_rnflut_pony (blue, weight) VALUES (1, 1)"
                    )
            cursor.execute("DELETE FROM test_rnflut_pony")
        # Reversal.
        with connection.schema_editor() as editor:
            operation.database_backwards(
                "test_rnflut", editor, new_state, project_state
            )
        self.assertColumnExists("test_rnflut_pony", "pink")
        self.assertColumnNotExists("test_rnflut_pony", "blue")