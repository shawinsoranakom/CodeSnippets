def test_alter_field_add_database_default_func(self):
        app_label = "test_alfladdf"
        project_state = self.set_up_test_model(app_label)
        operation = migrations.AlterField(
            "Pony", "weight", models.FloatField(db_default=Pi())
        )
        new_state = project_state.clone()
        operation.state_forwards(app_label, new_state)
        old_weight = project_state.models[app_label, "pony"].fields["weight"]
        self.assertIs(old_weight.default, models.NOT_PROVIDED)
        self.assertIs(old_weight.db_default, models.NOT_PROVIDED)
        new_weight = new_state.models[app_label, "pony"].fields["weight"]
        self.assertIs(new_weight.default, models.NOT_PROVIDED)
        self.assertIsInstance(new_weight.db_default, Pi)
        pony = project_state.apps.get_model(app_label, "pony").objects.create(weight=1)
        self.assertEqual(pony.weight, 1)
        # Alter field.
        with connection.schema_editor() as editor:
            operation.database_forwards(app_label, editor, project_state, new_state)
        pony = new_state.apps.get_model(app_label, "pony").objects.create()
        if not connection.features.can_return_columns_from_insert:
            pony.refresh_from_db()
        self.assertAlmostEqual(pony.weight, math.pi)
        # Reversal.
        with connection.schema_editor() as editor:
            operation.database_backwards(app_label, editor, new_state, project_state)
        pony = project_state.apps.get_model(app_label, "pony").objects.create(weight=1)
        self.assertEqual(pony.weight, 1)