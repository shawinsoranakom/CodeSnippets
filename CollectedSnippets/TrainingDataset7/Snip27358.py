def test_alter_field_change_default_to_database_default(self):
        """The AlterField operation changing default to db_default."""
        app_label = "test_alflcdtdd"
        project_state = self.set_up_test_model(app_label)
        operation = migrations.AlterField(
            "Pony", "pink", models.IntegerField(db_default=4)
        )
        new_state = project_state.clone()
        operation.state_forwards(app_label, new_state)
        old_pink = project_state.models[app_label, "pony"].fields["pink"]
        self.assertEqual(old_pink.default, 3)
        self.assertIs(old_pink.db_default, models.NOT_PROVIDED)
        new_pink = new_state.models[app_label, "pony"].fields["pink"]
        self.assertIs(new_pink.default, models.NOT_PROVIDED)
        self.assertEqual(new_pink.db_default, 4)
        pony = project_state.apps.get_model(app_label, "pony").objects.create(weight=1)
        self.assertEqual(pony.pink, 3)
        # Alter field.
        with connection.schema_editor() as editor:
            operation.database_forwards(app_label, editor, project_state, new_state)
        pony = new_state.apps.get_model(app_label, "pony").objects.create(weight=1)
        if not connection.features.can_return_columns_from_insert:
            pony.refresh_from_db()
        self.assertEqual(pony.pink, 4)
        # Reversal.
        with connection.schema_editor() as editor:
            operation.database_backwards(app_label, editor, new_state, project_state)
        pony = project_state.apps.get_model(app_label, "pony").objects.create(weight=1)
        self.assertEqual(pony.pink, 3)