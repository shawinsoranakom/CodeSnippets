def test_alias_annotate_with_aggregation(self):
        qs = Book.objects.alias(
            is_book_alias=Value(1),
            rating_count_alias=Count("rating"),
        ).annotate(
            is_book=F("is_book_alias"),
            rating_count=F("rating_count_alias"),
        )
        book = qs.first()
        self.assertIs(hasattr(book, "is_book_alias"), False)
        self.assertIs(hasattr(book, "rating_count_alias"), False)
        for book in qs:
            with self.subTest(book=book):
                self.assertEqual(book.is_book, 1)
                self.assertEqual(book.rating_count, 1)