def test_run_sql_migrate_foo_router_with_hints(self):
        self._test_run_sql("test_mltdb_runsql3", should_run=True, hints={"foo": True})