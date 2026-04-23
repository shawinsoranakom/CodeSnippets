def test_for_update_sql_generated_nowait(self):
        """
        The backend's FOR UPDATE NOWAIT variant appears in
        generated SQL when select_for_update is invoked.
        """
        with transaction.atomic(), CaptureQueriesContext(connection) as ctx:
            list(Person.objects.select_for_update(nowait=True))
        self.assertTrue(self.has_for_update_sql(ctx.captured_queries, nowait=True))