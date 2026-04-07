def test_serialize_deprecation(self, serialize_db_to_string, *mocked_objects):
        test_connection = get_connection_copy()
        creation = test_connection.creation_class(test_connection)
        self.patch_close_connection(creation)
        old_database_name = test_connection.settings_dict["NAME"]
        msg = (
            "DatabaseCreation.create_test_db(serialize) is deprecated. Call "
            "DatabaseCreation.serialize_test_db() once all test databases are set up "
            "instead if you need fixtures persistence between tests."
        )
        try:
            with (
                self.assertWarnsMessage(RemovedInDjango70Warning, msg) as ctx,
                mock.patch.object(creation, "_create_test_db"),
            ):
                creation.create_test_db(verbosity=0, serialize=True)
            self.assertEqual(ctx.filename, __file__)
            serialize_db_to_string.assert_called_once_with()
        finally:
            with mock.patch.object(creation, "_destroy_test_db"):
                creation.destroy_test_db(old_database_name, verbosity=0)
        # Now with `serialize` False.
        serialize_db_to_string.reset_mock()
        try:
            with (
                self.assertWarnsMessage(RemovedInDjango70Warning, msg) as ctx,
                mock.patch.object(creation, "_create_test_db"),
            ):
                creation.create_test_db(verbosity=0, serialize=False)
            self.assertEqual(ctx.filename, __file__)
            serialize_db_to_string.assert_not_called()
        finally:
            with mock.patch.object(creation, "_destroy_test_db"):
                creation.destroy_test_db(old_database_name, verbosity=0)