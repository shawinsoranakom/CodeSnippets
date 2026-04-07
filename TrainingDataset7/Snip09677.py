def _get_test_db_name(self):
        """
        Return the 'production' DB name to get the test DB creation machinery
        to work. This isn't a great deal in this case because DB names as
        handled by Django don't have real counterparts in Oracle.
        """
        return self.connection.settings_dict["NAME"]