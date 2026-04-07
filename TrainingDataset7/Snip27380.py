def test_rename_field_index_together(self):
        app_label = "test_rnflit"
        operations = [
            migrations.CreateModel(
                "Pony",
                fields=[
                    ("id", models.AutoField(primary_key=True)),
                    ("pink", models.IntegerField(default=3)),
                    ("weight", models.FloatField()),
                ],
                options={
                    "index_together": {("weight", "pink")},
                },
            ),
        ]
        project_state = self.apply_operations(app_label, ProjectState(), operations)

        operation = migrations.RenameField("Pony", "pink", "blue")
        new_state = project_state.clone()
        operation.state_forwards("test_rnflit", new_state)
        self.assertIn("blue", new_state.models["test_rnflit", "pony"].fields)
        self.assertNotIn("pink", new_state.models["test_rnflit", "pony"].fields)
        # index_together has the renamed column.
        self.assertIn(
            "blue",
            list(new_state.models["test_rnflit", "pony"].options["index_together"])[0],
        )
        self.assertNotIn(
            "pink",
            list(new_state.models["test_rnflit", "pony"].options["index_together"])[0],
        )

        # Rename field.
        self.assertColumnExists("test_rnflit_pony", "pink")
        self.assertColumnNotExists("test_rnflit_pony", "blue")
        with connection.schema_editor() as editor:
            operation.database_forwards("test_rnflit", editor, project_state, new_state)
        self.assertColumnExists("test_rnflit_pony", "blue")
        self.assertColumnNotExists("test_rnflit_pony", "pink")
        # The index constraint has been ported over.
        self.assertIndexExists("test_rnflit_pony", ["weight", "blue"])
        # Reversal.
        with connection.schema_editor() as editor:
            operation.database_backwards(
                "test_rnflit", editor, new_state, project_state
            )
        self.assertIndexExists("test_rnflit_pony", ["weight", "pink"])