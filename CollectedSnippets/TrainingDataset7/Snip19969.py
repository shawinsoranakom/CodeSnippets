def test_sql_queries(self):
        """
        Test whether sql_queries represents the actual amount
        of queries executed. (#23364)
        """
        url = "/debug/"
        response = self.client.get(url)
        self.assertContains(response, "First query list: 0")
        self.assertContains(response, "Second query list: 1")
        # Check we have not actually memoized connection.queries
        self.assertContains(response, "Third query list: 2")
        # Check queries for DB connection 'other'
        self.assertContains(response, "Fourth query list: 3")