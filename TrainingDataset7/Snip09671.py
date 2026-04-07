def _test_database_tblspace_tmp_maxsize(self):
        return self._test_settings_get("DATAFILE_TMP_MAXSIZE", default="500M")