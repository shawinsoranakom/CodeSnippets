def test_alter_field_change_nullable_to_database_default_not_null(self):
        """
        The AlterField operation changing a null field to db_default.
        """
        app_label = "test_alflcntddnn"
        project_state = self.set_up_test_model(app_label)
        operation = migrations.AlterField(
            "Pony", "green", models.IntegerField(db_default=4)
        )
        new_state = project_state.clone()
        operation.state_forwards(app_label, new_state)
        old_green = project_state.models[app_label, "pony"].fields["green"]
        self.assertIs(old_green.db_default, models.NOT_PROVIDED)
        new_green = new_state.models[app_label, "pony"].fields["green"]
        self.assertEqual(new_green.db_default, 4)
        old_pony = project_state.apps.get_model(app_label, "pony").objects.create(
            weight=1
        )
        self.assertIsNone(old_pony.green)
        # Alter field.
        with connection.schema_editor() as editor:
            operation.database_forwards(app_label, editor, project_state, new_state)
        old_pony.refresh_from_db()
        self.assertEqual(old_pony.green, 4)
        pony = new_state.apps.get_model(app_label, "pony").objects.create(weight=1)
        if not connection.features.can_return_columns_from_insert:
            pony.refresh_from_db()
        self.assertEqual(pony.green, 4)
        # Reversal.
        with connection.schema_editor() as editor:
            operation.database_backwards(app_label, editor, new_state, project_state)
        pony = project_state.apps.get_model(app_label, "pony").objects.create(weight=1)
        self.assertIsNone(pony.green)