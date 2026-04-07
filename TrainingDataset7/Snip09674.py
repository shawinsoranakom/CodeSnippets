def _test_database_tblspace_extsize(self):
        return self._test_settings_get("DATAFILE_EXTSIZE", default="25M")