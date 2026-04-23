def test_FK_raw_query(self):
        """
        Test of a simple raw query against a model containing a foreign key
        """
        query = "SELECT * FROM raw_query_book"
        books = Book.objects.all()
        self.assertSuccessfulRawQuery(Book, query, books)