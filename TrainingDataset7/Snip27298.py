def test_run_python_migrate_foo_router_with_hints(self):
        self._test_run_python(
            "test_mltdb_runpython3", should_run=True, hints={"foo": True}
        )