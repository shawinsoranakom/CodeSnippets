def test_translations(self):
        """
        Test of raw query's optional ability to translate unexpected result
        column names to specific model fields
        """
        query = (
            "SELECT first_name AS first, last_name AS last, dob, id "
            "FROM raw_query_author"
        )
        translations = {"first": "first_name", "last": "last_name"}
        authors = Author.objects.all()
        self.assertSuccessfulRawQuery(Author, query, authors, translations=translations)