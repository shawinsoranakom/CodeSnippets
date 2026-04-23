def test_bool(self):
        self.assertIs(bool(Book.objects.raw("SELECT * FROM raw_query_book")), True)
        self.assertIs(
            bool(Book.objects.raw("SELECT * FROM raw_query_book WHERE id = 0")), False
        )