def test_eq_func(self):
        index = models.Index(Lower("title"), models.F("author"), name="book_func_idx")
        same_index = models.Index(Lower("title"), "author", name="book_func_idx")
        another_index = models.Index(Lower("title"), name="book_func_idx")
        self.assertEqual(index, same_index)
        self.assertEqual(index, mock.ANY)
        self.assertNotEqual(index, another_index)