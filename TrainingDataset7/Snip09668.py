def _test_database_tblspace_datafile(self):
        tblspace = "%s.dbf" % self._test_database_tblspace()
        return self._test_settings_get("DATAFILE", default=tblspace)