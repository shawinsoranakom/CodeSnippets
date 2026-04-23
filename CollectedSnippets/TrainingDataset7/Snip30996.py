def test_len(self):
        self.assertEqual(len(Book.objects.raw("SELECT * FROM raw_query_book")), 4)
        self.assertEqual(
            len(Book.objects.raw("SELECT * FROM raw_query_book WHERE id = 0")), 0
        )