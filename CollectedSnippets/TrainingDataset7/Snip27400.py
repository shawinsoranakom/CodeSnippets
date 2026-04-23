def test_rename_index_state_forwards_unnamed_index(self):
        app_label = "test_rnidsfui"
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
        old_model = project_state.apps.get_model(app_label, "Pony")
        new_state = project_state.clone()

        operation = migrations.RenameIndex(
            "Pony", new_name="new_pony_pink_idx", old_fields=("weight", "pink")
        )
        operation.state_forwards(app_label, new_state)
        new_model = new_state.apps.get_model(app_label, "Pony")
        self.assertIsNot(old_model, new_model)
        self.assertEqual(new_model._meta.indexes[0].name, "new_pony_pink_idx")