def test_migrate_test_setting_false_ensure_schema(
        self,
        mocked_ensure_schema,
        mocked_sync_apps,
        *mocked_objects,
    ):
        test_connection = get_connection_copy()
        test_connection.settings_dict["TEST"]["MIGRATE"] = False
        creation = test_connection.creation_class(test_connection)
        self.patch_close_connection(creation)
        old_database_name = test_connection.settings_dict["NAME"]
        try:
            with mock.patch.object(creation, "_create_test_db"):
                creation.create_test_db(verbosity=0, autoclobber=True)
            # The django_migrations table is not created.
            mocked_ensure_schema.assert_not_called()
            # App is synced.
            mocked_sync_apps.assert_called()
            mocked_args, _ = mocked_sync_apps.call_args
            self.assertEqual(mocked_args[1], {"app_unmigrated"})
        finally:
            with mock.patch.object(creation, "_destroy_test_db"):
                creation.destroy_test_db(old_database_name, verbosity=0)