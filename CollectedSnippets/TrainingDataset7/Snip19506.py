def test_run_checks_database_exclusion(self):
        registry = CheckRegistry()

        database_errors = [checks.Warning("Database Check")]

        @registry.register(Tags.database)
        def database_system_check(**kwargs):
            return database_errors

        errors = registry.run_checks()
        self.assertEqual(errors, [])

        errors = registry.run_checks(databases=["default"])
        self.assertEqual(errors, database_errors)