def test_extra_conversions(self):
        """Extra translations are ignored."""
        query = "SELECT * FROM raw_query_author"
        translations = {"something": "else"}
        authors = Author.objects.all()
        self.assertSuccessfulRawQuery(Author, query, authors, translations=translations)