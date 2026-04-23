def test_default_related_name(self):
        self.assertEqual(list(self.author.books.all()), [self.book])