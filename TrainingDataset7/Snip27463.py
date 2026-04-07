def test_add_field_after_generated_field(self):
        app_label = "test_adfagf"
        project_state = self.set_up_test_model(app_label)
        operation_1 = migrations.AddField(
            "Pony",
            "generated",
            models.GeneratedField(
                expression=Value(1),
                output_field=models.IntegerField(),
                db_persist=True,
            ),
        )
        operation_2 = migrations.AddField(
            "Pony",
            "static",
            models.IntegerField(default=2),
        )
        new_state = project_state.clone()
        operation_1.state_forwards(app_label, new_state)
        with connection.schema_editor() as editor:
            operation_1.database_forwards(app_label, editor, project_state, new_state)
        project_state, new_state = new_state, new_state.clone()
        pony_old = new_state.apps.get_model(app_label, "Pony").objects.create(weight=20)
        self.assertEqual(pony_old.generated, 1)
        operation_2.state_forwards(app_label, new_state)
        with connection.schema_editor() as editor:
            operation_2.database_forwards(app_label, editor, project_state, new_state)
        Pony = new_state.apps.get_model(app_label, "Pony")
        pony_old = Pony.objects.get(pk=pony_old.pk)
        self.assertEqual(pony_old.generated, 1)
        self.assertEqual(pony_old.static, 2)
        pony_new = Pony.objects.create(weight=20)
        self.assertEqual(pony_new.generated, 1)
        self.assertEqual(pony_new.static, 2)