def _test_database_tblspace_tmp_extsize(self):
        return self._test_settings_get("DATAFILE_TMP_EXTSIZE", default="25M")