def destroy_test_db(
        self, old_database_name=None, verbosity=1, keepdb=False, suffix=None
    ):
        """
        Destroy a test database, prompting the user for confirmation if the
        database already exists.
        """
        self.connection.close()
        if suffix is None:
            test_database_name = self.connection.settings_dict["NAME"]
        else:
            test_database_name = self.get_test_db_clone_settings(suffix)["NAME"]

        if verbosity >= 1:
            action = "Destroying"
            if keepdb:
                action = "Preserving"
            self.log(
                "%s test database for alias %s..."
                % (
                    action,
                    self._get_database_display_str(verbosity, test_database_name),
                )
            )

        # if we want to preserve the database
        # skip the actual destroying piece.
        if not keepdb:
            self._destroy_test_db(test_database_name, verbosity)

        # Restore the original database name
        if old_database_name is not None:
            settings.DATABASES[self.connection.alias]["NAME"] = old_database_name
            self.connection.settings_dict["NAME"] = old_database_name