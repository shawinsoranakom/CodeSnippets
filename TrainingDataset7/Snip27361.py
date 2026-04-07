def test_alter_field_change_nullable_to_decimal_database_default_not_null(self):
        app_label = "test_alflcntdddn"
        project_state = self.set_up_test_model(app_label)
        operation_1 = migrations.AddField(
            "Pony",
            "height",
            models.DecimalField(null=True, max_digits=5, decimal_places=2),
        )
        operation_2 = migrations.AlterField(
            "Pony",
            "height",
            models.DecimalField(
                max_digits=5, decimal_places=2, db_default=Decimal("12.22")
            ),
        )
        table_name = f"{app_label}_pony"
        self.assertColumnNotExists(table_name, "height")
        # Add field.
        new_state = project_state.clone()
        operation_1.state_forwards(app_label, new_state)
        with connection.schema_editor() as editor:
            operation_1.database_forwards(app_label, editor, project_state, new_state)
        self.assertColumnExists(table_name, "height")
        old_pony = new_state.apps.get_model(app_label, "pony").objects.create(weight=1)
        self.assertIsNone(old_pony.height)
        # Alter field.
        project_state, new_state = new_state, new_state.clone()
        operation_2.state_forwards(app_label, new_state)
        with connection.schema_editor() as editor:
            operation_2.database_forwards(app_label, editor, project_state, new_state)
        old_pony.refresh_from_db()
        self.assertEqual(old_pony.height, Decimal("12.22"))
        pony = new_state.apps.get_model(app_label, "pony").objects.create(weight=2)
        if not connection.features.can_return_columns_from_insert:
            pony.refresh_from_db()
        self.assertEqual(pony.height, Decimal("12.22"))