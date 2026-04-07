def test_add_field_both_defaults(self):
        """The AddField operation with both default and db_default."""
        app_label = "test_adflbddd"
        table_name = f"{app_label}_pony"
        project_state = self.set_up_test_model(app_label)
        operation = migrations.AddField(
            "Pony", "height", models.FloatField(default=3, db_default=4)
        )
        new_state = project_state.clone()
        operation.state_forwards(app_label, new_state)
        self.assertEqual(len(new_state.models[app_label, "pony"].fields), 6)
        field = new_state.models[app_label, "pony"].fields["height"]
        self.assertEqual(field.default, 3)
        self.assertEqual(field.db_default, 4)
        pre_pony_pk = (
            project_state.apps.get_model(app_label, "pony").objects.create(weight=4).pk
        )
        self.assertColumnNotExists(table_name, "height")
        # Add field.
        with connection.schema_editor() as editor:
            operation.database_forwards(app_label, editor, project_state, new_state)
        self.assertColumnExists(table_name, "height")
        post_pony_pk = (
            project_state.apps.get_model(app_label, "pony").objects.create(weight=10).pk
        )
        new_model = new_state.apps.get_model(app_label, "pony")
        pre_pony = new_model.objects.get(pk=pre_pony_pk)
        self.assertEqual(pre_pony.height, 4)
        post_pony = new_model.objects.get(pk=post_pony_pk)
        self.assertEqual(post_pony.height, 4)
        new_pony = new_model.objects.create(weight=5)
        if not connection.features.can_return_columns_from_insert:
            new_pony.refresh_from_db()
        self.assertEqual(new_pony.height, 3)
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