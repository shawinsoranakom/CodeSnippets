def test_basic_alias_annotation(self):
        qs = Book.objects.alias(
            is_book_alias=Value(1),
        ).annotate(is_book=F("is_book_alias"))
        self.assertIs(hasattr(qs.first(), "is_book_alias"), False)
        for book in qs:
            with self.subTest(book=book):
                self.assertEqual(book.is_book, 1)