def _test_settings_get(self, key, default=None, prefixed=None):
        """
        Return a value from the test settings dict, or a given default, or a
        prefixed entry from the main settings dict.
        """
        settings_dict = self.connection.settings_dict
        val = settings_dict["TEST"].get(key, default)
        if val is None and prefixed:
            val = TEST_DATABASE_PREFIX + settings_dict[prefixed]
        return val