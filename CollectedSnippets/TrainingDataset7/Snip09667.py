def _test_database_tblspace_tmp(self):
        settings_dict = self.connection.settings_dict
        return settings_dict["TEST"].get(
            "TBLSPACE_TMP", TEST_DATABASE_PREFIX + settings_dict["USER"] + "_temp"
        )