def test_iterator(self):
        with self.assertNumQueries(2):
            books = Book.objects.raw("SELECT * FROM raw_query_book")
            list(books.iterator())
            list(books.iterator())