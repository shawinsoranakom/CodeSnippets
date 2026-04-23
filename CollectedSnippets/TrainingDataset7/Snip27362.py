def test_alter_field_change_blank_nullable_database_default_to_not_null(self):
        app_label = "test_alflcbnddnn"
        table_name = f"{app_label}_pony"
        project_state = self.set_up_test_model(app_label)
        default = "Yellow"
        operation = migrations.AlterField(
            "Pony",
            "yellow",
            models.CharField(blank=True, db_default=default, max_length=20),
        )
        new_state = project_state.clone()
        operation.state_forwards(app_label, new_state)
        self.assertColumnNull(table_name, "yellow")
        pony = project_state.apps.get_model(app_label, "pony").objects.create(
            weight=1, yellow=None
        )
        self.assertIsNone(pony.yellow)
        # Alter field.
        with connection.schema_editor() as editor:
            operation.database_forwards(app_label, editor, project_state, new_state)
        self.assertColumnNotNull(table_name, "yellow")
        pony.refresh_from_db()
        self.assertEqual(pony.yellow, default)
        pony = new_state.apps.get_model(app_label, "pony").objects.create(weight=1)
        if not connection.features.can_return_columns_from_insert:
            pony.refresh_from_db()
        self.assertEqual(pony.yellow, default)
        # Reversal.
        with connection.schema_editor() as editor:
            operation.database_backwards(app_label, editor, new_state, project_state)
        self.assertColumnNull(table_name, "yellow")
        pony = project_state.apps.get_model(app_label, "pony").objects.create(
            weight=1, yellow=None
        )
        self.assertIsNone(pony.yellow)