def test_white_space_query(self):
        query = "    SELECT * FROM raw_query_author"
        authors = Author.objects.all()
        self.assertSuccessfulRawQuery(Author, query, authors)