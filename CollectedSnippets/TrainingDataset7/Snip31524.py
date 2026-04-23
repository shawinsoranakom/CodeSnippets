def test_for_update_sql_generated_skip_locked(self):
        """
        The backend's FOR UPDATE SKIP LOCKED variant appears in
        generated SQL when select_for_update is invoked.
        """
        with transaction.atomic(), CaptureQueriesContext(connection) as ctx:
            list(Person.objects.select_for_update(skip_locked=True))
        self.assertTrue(self.has_for_update_sql(ctx.captured_queries, skip_locked=True))