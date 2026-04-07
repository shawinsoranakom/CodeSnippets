def test_eq(self):
        index = models.Index(fields=["title"])
        same_index = models.Index(fields=["title"])
        another_index = models.Index(fields=["title", "author"])
        index.model = Book
        same_index.model = Book
        another_index.model = Book
        self.assertEqual(index, same_index)
        self.assertEqual(index, mock.ANY)
        self.assertNotEqual(index, another_index)