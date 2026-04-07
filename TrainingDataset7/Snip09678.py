def test_db_signature(self):
        settings_dict = self.connection.settings_dict
        return (
            settings_dict["HOST"],
            settings_dict["PORT"],
            settings_dict["ENGINE"],
            settings_dict["NAME"],
            self._test_database_user(),
        )