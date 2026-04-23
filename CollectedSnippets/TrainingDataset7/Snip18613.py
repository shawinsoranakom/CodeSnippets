def test_check_database_version_supported(self, mocked_get_database_version):
        msg = "Oracle 19 or later is required (found 18.1)."
        with self.assertRaisesMessage(NotSupportedError, msg):
            connection.check_database_version_supported()
        self.assertTrue(mocked_get_database_version.called)