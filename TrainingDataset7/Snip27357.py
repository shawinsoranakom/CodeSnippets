def test_alter_field_add_database_default(self):
        app_label = "test_alfladd"
        project_state = self.set_up_test_model(app_label)
        operation = migrations.AlterField(
            "Pony", "weight", models.FloatField(db_default=4.5)
        )
        new_state = project_state.clone()
        operation.state_forwards(app_label, new_state)
        old_weight = project_state.models[app_label, "pony"].fields["weight"]
        self.assertIs(old_weight.db_default, models.NOT_PROVIDED)
        new_weight = new_state.models[app_label, "pony"].fields["weight"]
        self.assertEqual(new_weight.db_default, 4.5)
        with self.assertRaises(IntegrityError), transaction.atomic():
            project_state.apps.get_model(app_label, "pony").objects.create()
        # Alter field.
        with connection.schema_editor() as editor:
            operation.database_forwards(app_label, editor, project_state, new_state)
        pony = new_state.apps.get_model(app_label, "pony").objects.create()
        if not connection.features.can_return_columns_from_insert:
            pony.refresh_from_db()
        self.assertEqual(pony.weight, 4.5)
        # Reversal.
        with connection.schema_editor() as editor:
            operation.database_backwards(app_label, editor, new_state, project_state)
        with self.assertRaises(IntegrityError), transaction.atomic():
            project_state.apps.get_model(app_label, "pony").objects.create()
        # Deconstruction.
        definition = operation.deconstruct()
        self.assertEqual(definition[0], "AlterField")
        self.assertEqual(definition[1], [])
        self.assertEqual(
            definition[2],
            {
                "field": new_weight,
                "model_name": "Pony",
                "name": "weight",
            },
        )