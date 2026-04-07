def test_check_database_version_supported(self, mocked_get_database_version):
        if connection.mysql_is_mariadb:
            mocked_get_database_version.return_value = (10, 10)
            msg = "MariaDB 10.11 or later is required (found 10.10)."
        else:
            mocked_get_database_version.return_value = (8, 0, 31)
            msg = "MySQL 8.4 or later is required (found 8.0.31)."

        with self.assertRaisesMessage(NotSupportedError, msg):
            connection.check_database_version_supported()
        self.assertTrue(mocked_get_database_version.called)