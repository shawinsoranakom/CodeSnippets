def test_simple_raw_query(self):
        """
        Basic test of raw query with a simple database query
        """
        query = "SELECT * FROM raw_query_author"
        authors = Author.objects.all()
        self.assertSuccessfulRawQuery(Author, query, authors)