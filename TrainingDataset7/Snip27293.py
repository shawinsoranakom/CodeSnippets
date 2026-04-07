def test_run_sql_migrate_foo_router_without_hints(self):
        self._test_run_sql("test_mltdb_runsql2", should_run=False)