def _test_run_sql(self, app_label, should_run, hints=None):
        with override_settings(DATABASE_ROUTERS=[MigrateEverythingRouter()]):
            project_state = self.set_up_test_model(app_label)

        sql = """
        INSERT INTO {0}_pony (pink, weight) VALUES (1, 3.55);
        INSERT INTO {0}_pony (pink, weight) VALUES (3, 5.0);
        """.format(app_label)

        operation = migrations.RunSQL(sql, hints=hints or {})
        # Test the state alteration does nothing
        new_state = project_state.clone()
        operation.state_forwards(app_label, new_state)
        self.assertEqual(new_state, project_state)
        # Test the database alteration
        self.assertEqual(
            project_state.apps.get_model(app_label, "Pony").objects.count(), 0
        )
        with connection.schema_editor() as editor:
            operation.database_forwards(app_label, editor, project_state, new_state)
        Pony = project_state.apps.get_model(app_label, "Pony")
        if should_run:
            self.assertEqual(Pony.objects.count(), 2)
        else:
            self.assertEqual(Pony.objects.count(), 0)