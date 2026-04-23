def get_test_db_clone_settings(self, suffix):
        """
        Return a modified connection settings dict for the n-th clone of a DB.
        """
        # When this function is called, the test database has been created
        # already and its name has been copied to settings_dict['NAME'] so
        # we don't need to call _get_test_db_name.
        orig_settings_dict = self.connection.settings_dict
        return {
            **orig_settings_dict,
            "NAME": "{}_{}".format(orig_settings_dict["NAME"], suffix),
        }