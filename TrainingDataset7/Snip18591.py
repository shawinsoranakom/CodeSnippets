def _test_database_passwd(self):
        # Mocked to avoid test user password changed
        return connection.settings_dict["SAVED_PASSWORD"]