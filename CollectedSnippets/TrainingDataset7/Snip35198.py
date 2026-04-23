def test_queries_cleared(self):
        """
        TransactionTestCase._pre_setup() clears the connections' queries_log
        so that it's less likely to overflow. An overflow causes
        assertNumQueries() to fail.
        """
        for alias in self.databases:
            self.assertEqual(
                len(connections[alias].queries_log), 0, "Failed for alias %s" % alias
            )