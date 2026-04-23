def _test_database_oracle_managed_files(self):
        return self._test_settings_get("ORACLE_MANAGED_FILES", default=False)