def test_disallowed_thread_database_connection(self):
        expected_message = (
            "Database threaded connections to 'default' are not allowed in "
            "SimpleTestCase subclasses. Either subclass TestCase or TransactionTestCase"
            " to ensure proper test isolation or add 'default' to "
            "test_utils.tests.DisallowedDatabaseQueriesTests.databases to "
            "silence this failure."
        )

        exceptions = []

        def thread_func():
            try:
                Car.objects.first()
            except DatabaseOperationForbidden as e:
                exceptions.append(e)

        t = threading.Thread(target=thread_func)
        t.start()
        t.join()
        self.assertEqual(len(exceptions), 1)
        self.assertEqual(exceptions[0].args[0], expected_message)