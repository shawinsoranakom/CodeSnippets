def run_tests(self, test_labels, **kwargs):
        """
        Run the unit tests for all the test labels in the provided list.

        Test labels should be dotted Python paths to test modules, test
        classes, or test methods.

        Return the number of tests that failed.
        """
        self.setup_test_environment()
        suite = self.build_suite(test_labels)
        databases = self.get_databases(suite)
        suite.serialized_aliases = set(
            alias for alias, serialize in databases.items() if serialize
        )
        suite.used_aliases = set(databases)
        with self.time_keeper.timed("Total database setup"):
            old_config = self.setup_databases(
                aliases=databases,
                serialized_aliases=suite.serialized_aliases,
            )
        run_failed = False
        try:
            self.run_checks(databases)
            result = self.run_suite(suite)
        except Exception:
            run_failed = True
            raise
        finally:
            try:
                with self.time_keeper.timed("Total database teardown"):
                    self.teardown_databases(old_config)
                self.teardown_test_environment()
            except Exception:
                # Silence teardown exceptions if an exception was raised during
                # runs to avoid shadowing it.
                if not run_failed:
                    raise
        self.time_keeper.print_results()
        return self.suite_result(suite, result)