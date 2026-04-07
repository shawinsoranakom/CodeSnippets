def test_rename_index_unnamed_index(self):
        app_label = "test_rninui"
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
        table_name = app_label + "_pony"
        self.assertIndexNameNotExists(table_name, "new_pony_test_idx")
        operation = migrations.RenameIndex(
            "Pony", new_name="new_pony_test_idx", old_fields=("weight", "pink")
        )
        self.assertEqual(
            operation.describe(),
            "Rename unnamed index for ('weight', 'pink') on Pony to new_pony_test_idx",
        )
        self.assertEqual(
            operation.migration_name_fragment,
            "rename_pony_weight_pink_new_pony_test_idx",
        )
        new_state = project_state.clone()
        operation.state_forwards(app_label, new_state)
        # Ensure the model state has the correct type for the index_together
        # option.
        self.assertIsInstance(
            new_state.models[app_label, "pony"].options["index_together"], set
        )
        # Rename index.
        with connection.schema_editor() as editor:
            operation.database_forwards(app_label, editor, project_state, new_state)
        self.assertIndexNameExists(table_name, "new_pony_test_idx")
        # Reverse is a no-op.
        with connection.schema_editor() as editor, self.assertNumQueries(0):
            operation.database_backwards(app_label, editor, new_state, project_state)
        self.assertIndexNameExists(table_name, "new_pony_test_idx")
        # Reapply, RenameIndex operation is a noop when the old and new name
        # match.
        with connection.schema_editor() as editor:
            operation.database_forwards(app_label, editor, new_state, project_state)
        self.assertIndexNameExists(table_name, "new_pony_test_idx")
        # Deconstruction.
        definition = operation.deconstruct()
        self.assertEqual(definition[0], "RenameIndex")
        self.assertEqual(definition[1], [])
        self.assertEqual(
            definition[2],
            {
                "model_name": "Pony",
                "new_name": "new_pony_test_idx",
                "old_fields": ("weight", "pink"),
            },
        )