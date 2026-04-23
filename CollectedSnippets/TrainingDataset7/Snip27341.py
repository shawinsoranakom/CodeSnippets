def test_add_field_database_default_special_char_escaping(self):
        app_label = "test_adflddsce"
        table_name = f"{app_label}_pony"
        project_state = self.set_up_test_model(app_label)
        old_pony_pk = (
            project_state.apps.get_model(app_label, "pony").objects.create(weight=4).pk
        )
        tests = ["%", "'", '"']
        for db_default in tests:
            with self.subTest(db_default=db_default):
                operation = migrations.AddField(
                    "Pony",
                    "special_char",
                    models.CharField(max_length=1, db_default=db_default),
                )
                new_state = project_state.clone()
                operation.state_forwards(app_label, new_state)
                self.assertEqual(len(new_state.models[app_label, "pony"].fields), 6)
                field = new_state.models[app_label, "pony"].fields["special_char"]
                self.assertEqual(field.default, models.NOT_PROVIDED)
                self.assertEqual(field.db_default, db_default)
                self.assertColumnNotExists(table_name, "special_char")
                with connection.schema_editor() as editor:
                    operation.database_forwards(
                        app_label, editor, project_state, new_state
                    )
                self.assertColumnExists(table_name, "special_char")
                new_model = new_state.apps.get_model(app_label, "pony")
                try:
                    new_pony = new_model.objects.create(weight=5)
                    if not connection.features.can_return_columns_from_insert:
                        new_pony.refresh_from_db()
                    self.assertEqual(new_pony.special_char, db_default)

                    old_pony = new_model.objects.get(pk=old_pony_pk)
                    if connection.vendor != "oracle" or db_default != "'":
                        # The single quotation mark ' is properly quoted and is
                        # set for new rows on Oracle, however it is not set on
                        # existing rows. Skip the assertion as it's probably a
                        # bug in Oracle.
                        self.assertEqual(old_pony.special_char, db_default)
                finally:
                    with connection.schema_editor() as editor:
                        operation.database_backwards(
                            app_label, editor, new_state, project_state
                        )