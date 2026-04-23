def test_alias_annotation_expression(self):
        qs = Book.objects.alias(
            is_book_alias=Value(1),
        ).annotate(is_book=Coalesce("is_book_alias", 0))
        self.assertIs(hasattr(qs.first(), "is_book_alias"), False)
        for book in qs:
            with self.subTest(book=book):
                self.assertEqual(book.is_book, 1)