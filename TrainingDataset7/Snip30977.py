def test_query_representation(self):
        """
        Test representation of raw query with parameters
        """
        query = "SELECT * FROM raw_query_author WHERE last_name = %(last)s"
        qset = Author.objects.raw(query, {"last": "foo"})
        self.assertEqual(
            repr(qset),
            "<RawQuerySet: SELECT * FROM raw_query_author WHERE last_name = foo>",
        )
        self.assertEqual(
            repr(qset.query),
            "<RawQuery: SELECT * FROM raw_query_author WHERE last_name = foo>",
        )

        query = "SELECT * FROM raw_query_author WHERE last_name = %s"
        qset = Author.objects.raw(query, {"foo"})
        self.assertEqual(
            repr(qset),
            "<RawQuerySet: SELECT * FROM raw_query_author WHERE last_name = foo>",
        )
        self.assertEqual(
            repr(qset.query),
            "<RawQuery: SELECT * FROM raw_query_author WHERE last_name = foo>",
        )