def clone_test_db(self, suffix, verbosity=1, autoclobber=False, keepdb=False):
        """
        Clone a test database.
        """
        source_database_name = self.connection.settings_dict["NAME"]

        if verbosity >= 1:
            action = "Cloning test database"
            if keepdb:
                action = "Using existing clone"
            self.log(
                "%s for alias %s..."
                % (
                    action,
                    self._get_database_display_str(verbosity, source_database_name),
                )
            )

        # We could skip this call if keepdb is True, but we instead
        # give it the keepdb param. See create_test_db for details.
        self._clone_test_db(suffix, verbosity, keepdb)