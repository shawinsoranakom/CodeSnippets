def test_migrate_test_setting_true(
        self, mocked_migrate, mocked_sync_apps, *mocked_objects
    ):
        test_connection = get_connection_copy()
        test_connection.settings_dict["TEST"]["MIGRATE"] = True
        creation = test_connection.creation_class(test_connection)
        self.patch_close_connection(creation)
        old_database_name = test_connection.settings_dict["NAME"]
        try:
            with mock.patch.object(creation, "_create_test_db"):
                creation.create_test_db(verbosity=0, autoclobber=True)
            # Migrations run.
            mocked_migrate.assert_called()
            args, kwargs = mocked_migrate.call_args
            self.assertEqual(args, ([("app_unmigrated", "0001_initial")],))
            self.assertEqual(len(kwargs["plan"]), 1)
            # App is not synced.
            mocked_sync_apps.assert_not_called()
        finally:
            with mock.patch.object(creation, "_destroy_test_db"):
                creation.destroy_test_db(old_database_name, verbosity=0)