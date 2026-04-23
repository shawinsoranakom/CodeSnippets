def test_add_field_database_default_function(self):
        app_label = "test_adflddf"
        table_name = f"{app_label}_pony"
        project_state = self.set_up_test_model(app_label)
        operation = migrations.AddField(
            "Pony", "height", models.FloatField(db_default=Pi())
        )
        new_state = project_state.clone()
        operation.state_forwards(app_label, new_state)
        self.assertEqual(len(new_state.models[app_label, "pony"].fields), 6)
        field = new_state.models[app_label, "pony"].fields["height"]
        self.assertEqual(field.default, models.NOT_PROVIDED)
        self.assertEqual(field.db_default, Pi())
        project_state.apps.get_model(app_label, "pony").objects.create(weight=4)
        self.assertColumnNotExists(table_name, "height")
        # Add field.
        with connection.schema_editor() as editor:
            operation.database_forwards(app_label, editor, project_state, new_state)
        self.assertColumnExists(table_name, "height")
        new_model = new_state.apps.get_model(app_label, "pony")
        old_pony = new_model.objects.get()
        self.assertAlmostEqual(old_pony.height, math.pi)
        new_pony = new_model.objects.create(weight=5)
        if not connection.features.can_return_columns_from_insert:
            new_pony.refresh_from_db()
        self.assertAlmostEqual(old_pony.height, math.pi)