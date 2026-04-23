def django_test_expected_failures(self):
        expected_failures = set()
        if self.uses_server_side_binding:
            expected_failures.update(
                {
                    # Parameters passed to expressions in SELECT and GROUP BY
                    # clauses are not recognized as the same values when using
                    # server-side binding cursors (#34255).
                    "aggregation.tests.AggregateTestCase."
                    "test_group_by_nested_expression_with_params",
                }
            )
        if not is_psycopg3:
            expected_failures.update(
                {
                    # operator does not exist: bigint[] = integer[]
                    "postgres_tests.test_array.TestQuerying.test_gt",
                    "postgres_tests.test_array.TestQuerying.test_in",
                    "postgres_tests.test_array.TestQuerying.test_lt",
                }
            )
        return expected_failures