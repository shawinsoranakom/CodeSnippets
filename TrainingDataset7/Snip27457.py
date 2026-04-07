def test_generated_field_changes_output_field(self):
        app_label = "test_gfcof"
        operation = migrations.AddField(
            "Pony",
            "modified_pink",
            models.GeneratedField(
                expression=F("pink") + F("pink"),
                output_field=models.IntegerField(),
                db_persist=True,
            ),
        )
        from_state, to_state = self.make_test_state(app_label, operation)
        # Add generated column.
        with connection.schema_editor() as editor:
            operation.database_forwards(app_label, editor, from_state, to_state)
        # Update output_field used in the generated field.
        operation = migrations.AlterField(
            "Pony",
            "modified_pink",
            models.GeneratedField(
                expression=F("pink") + F("pink"),
                output_field=models.DecimalField(decimal_places=2, max_digits=16),
                db_persist=True,
            ),
        )
        from_state = to_state.clone()
        to_state = self.apply_operations(app_label, from_state, [operation])
        with connection.schema_editor() as editor:
            operation.database_forwards(app_label, editor, from_state, to_state)