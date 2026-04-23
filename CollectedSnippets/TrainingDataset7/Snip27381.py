def test_rename_field_add_non_nullable_field_with_composite_pk(self):
        app_label = "test_rnfafnnwcpk"
        operations = [
            migrations.CreateModel(
                name="Release",
                fields=[
                    (
                        "pk",
                        models.CompositePrimaryKey("version", "name", primary_key=True),
                    ),
                    ("version", models.IntegerField()),
                    ("name", models.CharField(max_length=20)),
                ],
            ),
        ]
        project_state = self.apply_operations(app_label, ProjectState(), operations)
        new_state = project_state.clone()
        # Rename field used by CompositePrimaryKey.
        operation = migrations.RenameField("Release", "name", "renamed_field")
        operation.state_forwards(app_label, new_state)
        with connection.schema_editor() as editor:
            operation.database_forwards(app_label, editor, project_state, new_state)
        self.assertColumnExists(f"{app_label}_release", "renamed_field")
        project_state = new_state
        new_state = new_state.clone()
        # Add non-nullable field. Table is rebuilt on SQLite.
        operation = migrations.AddField(
            model_name="Release",
            name="new_non_nullable_field",
            field=models.CharField(default="x", max_length=20),
        )
        operation.state_forwards(app_label, new_state)
        with connection.schema_editor() as editor:
            operation.database_forwards(app_label, editor, project_state, new_state)
        self.assertColumnExists(f"{app_label}_release", "new_non_nullable_field")