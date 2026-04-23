def _test_database_tblspace_size(self):
        return self._test_settings_get("DATAFILE_SIZE", default="50M")