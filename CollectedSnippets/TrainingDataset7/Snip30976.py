def test_pyformat_params(self):
        """
        Test passing optional query parameters
        """
        query = "SELECT * FROM raw_query_author WHERE first_name = %(first)s"
        author = Author.objects.all()[2]
        params = {"first": author.first_name}
        qset = Author.objects.raw(query, params=params)
        results = list(qset)
        self.assertProcessed(Author, results, [author])
        self.assertNoAnnotations(results)
        self.assertEqual(len(results), 1)
        self.assertIsInstance(repr(qset), str)