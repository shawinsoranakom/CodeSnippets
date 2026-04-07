def test_for_update_sql_generated(self):
        """
        The backend's FOR UPDATE variant appears in
        generated SQL when select_for_update is invoked.
        """
        with transaction.atomic(), CaptureQueriesContext(connection) as ctx:
            list(Person.objects.select_for_update())
        self.assertTrue(self.has_for_update_sql(ctx.captured_queries))