def _get_databases(self, suite):
        databases = {}
        for test in iter_test_cases(suite):
            test_databases = getattr(test, "databases", None)
            if test_databases == "__all__":
                test_databases = connections
            if test_databases:
                serialized_rollback = getattr(test, "serialized_rollback", False)
                databases.update(
                    (alias, serialized_rollback or databases.get(alias, False))
                    for alias in test_databases
                )
        return databases