def test_overwrite_alias_with_annotation(self):
        qs = Book.objects.alias(is_book=Value(1)).annotate(is_book=F("is_book"))
        for book in qs:
            with self.subTest(book=book):
                self.assertEqual(book.is_book, 1)