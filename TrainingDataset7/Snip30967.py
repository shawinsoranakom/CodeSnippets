def test_fk_fetch_mode_peers(self):
        query = "SELECT * FROM raw_query_book"
        books = list(Book.objects.fetch_mode(FETCH_PEERS).raw(query))
        with self.assertNumQueries(1):
            books[0].author
            books[1].author