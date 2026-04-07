def test_update_sql_generated_no_key(self):
        """
        The backend's FOR NO KEY UPDATE variant appears in generated SQL when
        select_for_update() is invoked.
        """
        with transaction.atomic(), CaptureQueriesContext(connection) as ctx:
            list(Person.objects.select_for_update(no_key=True))
        self.assertIs(self.has_for_update_sql(ctx.captured_queries, no_key=True), True)