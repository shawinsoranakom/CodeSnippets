def _test_invalid_generated_field_changes_on_rename(self, db_persist):
        app_label = "test_igfcor"
        operation = migrations.AddField(
            "Pony",
            "modified_pink",
            models.GeneratedField(
                expression=F("pink") + F("pink"),
                output_field=models.IntegerField(),
                db_persist=db_persist,
            ),
        )
        project_state, new_state = self.make_test_state(app_label, operation)
        # Add generated column.
        with connection.schema_editor() as editor:
            operation.database_forwards(app_label, editor, project_state, new_state)
        # Rename field used in the generated field.
        operations = [
            migrations.RenameField("Pony", "pink", "renamed_pink"),
            migrations.AlterField(
                "Pony",
                "modified_pink",
                models.GeneratedField(
                    expression=F("renamed_pink"),
                    output_field=models.IntegerField(),
                    db_persist=db_persist,
                ),
            ),
        ]
        msg = (
            "Modifying GeneratedFields is not supported - the field "
            f"{app_label}.Pony.modified_pink must be removed and re-added with the "
            "new definition."
        )
        with self.assertRaisesMessage(ValueError, msg):
            self.apply_operations(app_label, new_state, operations)