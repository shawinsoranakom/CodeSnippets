def test_raw_query_lazy(self):
        """
        Raw queries are lazy: they aren't actually executed until they're
        iterated over.
        """
        q = Author.objects.raw("SELECT * FROM raw_query_author")
        self.assertIsNone(q.query.cursor)
        list(q)
        self.assertIsNotNone(q.query.cursor)