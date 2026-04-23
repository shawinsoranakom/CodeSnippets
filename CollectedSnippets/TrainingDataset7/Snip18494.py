def test_mark_expected_failures_and_skips_call(
        self, mark_expected_failures_and_skips, *mocked_objects
    ):
        """
        mark_expected_failures_and_skips() isn't called unless
        RUNNING_DJANGOS_TEST_SUITE is 'true'.
        """
        test_connection = get_connection_copy()
        creation = test_connection.creation_class(test_connection)
        self.patch_close_connection(creation)
        old_database_name = test_connection.settings_dict["NAME"]
        try:
            with mock.patch.object(creation, "_create_test_db"):
                creation.create_test_db(verbosity=0, autoclobber=True)
            self.assertIs(mark_expected_failures_and_skips.called, False)
        finally:
            with mock.patch.object(creation, "_destroy_test_db"):
                creation.destroy_test_db(old_database_name, verbosity=0)