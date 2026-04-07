def test_basic_annotation(self):
        books = Book.objects.annotate(is_book=Value(1))
        for book in books:
            self.assertEqual(book.is_book, 1)