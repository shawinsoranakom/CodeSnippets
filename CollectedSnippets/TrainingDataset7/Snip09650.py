def set_as_test_mirror(self, primary_settings_dict):
        """
        Set this database up to be used in testing as a mirror of a primary
        database whose settings are given.
        """
        self.connection.settings_dict["USER"] = primary_settings_dict["USER"]
        self.connection.settings_dict["PASSWORD"] = primary_settings_dict["PASSWORD"]