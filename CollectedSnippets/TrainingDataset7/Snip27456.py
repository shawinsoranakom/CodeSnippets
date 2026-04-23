def _test_add_generated_field(self, db_persist):
        app_label = "test_agf"
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
        self.assertColumnExists(f"{app_label}_pony", "modified_pink")
        Pony = new_state.apps.get_model(app_label, "Pony")
        obj = Pony.objects.create(pink=5, weight=3.23)
        self.assertEqual(obj.modified_pink, 10)
        # Reversal.
        with connection.schema_editor() as editor:
            operation.database_backwards(app_label, editor, new_state, project_state)
        self.assertColumnNotExists(f"{app_label}_pony", "modified_pink")