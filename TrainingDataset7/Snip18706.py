def test_get_test_db_clone_settings_not_supported(self, *mocked_objects):
        msg = "Cloning with start method 'unsupported' is not supported."
        with self.assertRaisesMessage(NotSupportedError, msg):
            connection.creation.get_test_db_clone_settings(1)