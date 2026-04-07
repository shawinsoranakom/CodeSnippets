def test_add_field_database_default(self):
        """The AddField operation can set and unset a database default."""
        app_label = "test_adfldd"
        table_name = f"{app_label}_pony"
        project_state = self.set_up_test_model(app_label)
        operation = migrations.AddField(
            "Pony", "height", models.FloatField(null=True, db_default=4)
        )
        new_state = project_state.clone()
        operation.state_forwards(app_label, new_state)
        self.assertEqual(len(new_state.models[app_label, "pony"].fields), 6)
        field = new_state.models[app_label, "pony"].fields["height"]
        self.assertEqual(field.default, models.NOT_PROVIDED)
        self.assertEqual(field.db_default, 4)
        project_state.apps.get_model(app_label, "pony").objects.create(weight=4)
        self.assertColumnNotExists(table_name, "height")
        # Add field.
        with connection.schema_editor() as editor:
            operation.database_forwards(app_label, editor, project_state, new_state)
        self.assertColumnExists(table_name, "height")
        new_model = new_state.apps.get_model(app_label, "pony")
        old_pony = new_model.objects.get()
        self.assertEqual(old_pony.height, 4)
        new_pony = new_model.objects.create(weight=5)
        if not connection.features.can_return_columns_from_insert:
            new_pony.refresh_from_db()
        self.assertEqual(new_pony.height, 4)
        # Reversal.
        with connection.schema_editor() as editor:
            operation.database_backwards(app_label, editor, new_state, project_state)
        self.assertColumnNotExists(table_name, "height")
        # Deconstruction.
        definition = operation.deconstruct()
        self.assertEqual(definition[0], "AddField")
        self.assertEqual(definition[1], [])
        self.assertEqual(
            definition[2],
            {
                "field": field,
                "model_name": "Pony",
                "name": "height",
            },
        )