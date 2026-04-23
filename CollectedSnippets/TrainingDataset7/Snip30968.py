def test_fk_fetch_mode_raise(self):
        query = "SELECT * FROM raw_query_book"
        books = list(Book.objects.fetch_mode(RAISE).raw(query))
        msg = "Fetching of Book.author blocked."
        with self.assertRaisesMessage(FieldFetchBlocked, msg) as cm:
            books[0].author
        self.assertIsNone(cm.exception.__cause__)
        self.assertTrue(cm.exception.__suppress_context__)