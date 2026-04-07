def _test_remove_generated_field(self, db_persist):
        app_label = "test_rgf"
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
        self.assertEqual(len(new_state.models[app_label, "pony"].fields), 6)
        # Add generated column.
        with connection.schema_editor() as editor:
            operation.database_forwards(app_label, editor, project_state, new_state)
        project_state = new_state
        new_state = project_state.clone()
        operation = migrations.RemoveField("Pony", "modified_pink")
        operation.state_forwards(app_label, new_state)
        # Remove generated column.
        with connection.schema_editor() as editor:
            operation.database_forwards(app_label, editor, project_state, new_state)
        self.assertColumnNotExists(f"{app_label}_pony", "modified_pink")