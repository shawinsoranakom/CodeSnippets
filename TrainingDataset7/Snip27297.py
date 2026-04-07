def test_run_python_migrate_foo_router_without_hints(self):
        self._test_run_python("test_mltdb_runpython2", should_run=False)