def test_result_caching(self):
        with self.assertNumQueries(1):
            books = Book.objects.raw("SELECT * FROM raw_query_book")
            list(books)
            list(books)