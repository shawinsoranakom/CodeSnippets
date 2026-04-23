def _test_database_tblspace_tmp_datafile(self):
        tblspace = "%s.dbf" % self._test_database_tblspace_tmp()
        return self._test_settings_get("DATAFILE_TMP", default=tblspace)