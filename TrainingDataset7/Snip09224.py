def create_test_db(
        self, verbosity=1, autoclobber=False, serialize=None, keepdb=False
    ):
        """
        Create a test database, prompting the user for confirmation if the
        database already exists. Return the name of the test database created.
        """
        # Don't import django.core.management if it isn't needed.
        from django.core.management import call_command

        test_database_name = self._get_test_db_name()

        if verbosity >= 1:
            action = "Creating"
            if keepdb:
                action = "Using existing"

            self.log(
                "%s test database for alias %s..."
                % (
                    action,
                    self._get_database_display_str(verbosity, test_database_name),
                )
            )

        # We could skip this call if keepdb is True, but we instead
        # give it the keepdb param. This is to handle the case
        # where the test DB doesn't exist, in which case we need to
        # create it, then just not destroy it. If we instead skip
        # this, we will get an exception.
        self._create_test_db(verbosity, autoclobber, keepdb)

        self.connection.close()
        settings.DATABASES[self.connection.alias]["NAME"] = test_database_name
        self.connection.settings_dict["NAME"] = test_database_name

        try:
            if self.connection.settings_dict["TEST"]["MIGRATE"] is False:
                # Disable migrations for all apps.
                old_migration_modules = settings.MIGRATION_MODULES
                settings.MIGRATION_MODULES = {
                    app.label: None for app in apps.get_app_configs()
                }
            # We report migrate messages at one level lower than that
            # requested. This ensures we don't get flooded with messages during
            # testing (unless you really ask to be flooded).
            call_command(
                "migrate",
                verbosity=max(verbosity - 1, 0),
                interactive=False,
                database=self.connection.alias,
                run_syncdb=True,
            )
        finally:
            if self.connection.settings_dict["TEST"]["MIGRATE"] is False:
                settings.MIGRATION_MODULES = old_migration_modules

        # We then serialize the current state of the database into a string
        # and store it on the connection. This slightly horrific process is so
        # people who are testing on databases without transactions or who are
        # using a TransactionTestCase still get a clean database on every test
        # run.
        if serialize is not None:
            warnings.warn(
                "DatabaseCreation.create_test_db(serialize) is deprecated. Call "
                "DatabaseCreation.serialize_test_db() once all test databases are set "
                "up instead if you need fixtures persistence between tests.",
                stacklevel=2,
                category=RemovedInDjango70Warning,
            )
            if serialize:
                self.connection._test_serialized_contents = (
                    self.serialize_db_to_string()
                )

        call_command("createcachetable", database=self.connection.alias)

        # Ensure a connection for the side effect of initializing the test
        # database.
        self.connection.ensure_connection()

        if os.environ.get("RUNNING_DJANGOS_TEST_SUITE") == "true":
            self.mark_expected_failures_and_skips()

        return test_database_name