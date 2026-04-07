def _test_database_tblspace_tmp_size(self):
        return self._test_settings_get("DATAFILE_TMP_SIZE", default="50M")