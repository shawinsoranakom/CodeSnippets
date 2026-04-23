def setUpClass(cls):
        # @skipIfDBFeature and @skipUnlessDBFeature cannot be chained. The
        # outermost takes precedence. Handle skipping manually instead.
        if connection.features.supports_timezones:
            raise SkipTest("Database has feature(s) supports_timezones")
        if not connection.features.test_db_allows_multiple_connections:
            raise SkipTest(
                "Database doesn't support feature(s): "
                "test_db_allows_multiple_connections"
            )

        super().setUpClass()