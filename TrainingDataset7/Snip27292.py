def test_run_sql_migrate_nothing_router(self):
        self._test_run_sql("test_mltdb_runsql", should_run=False)