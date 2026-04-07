def test_alias_after_annotation(self):
        qs = Book.objects.annotate(
            is_book=Value(1),
        ).alias(is_book_alias=F("is_book"))
        book = qs.first()
        self.assertIs(hasattr(book, "is_book"), True)
        self.assertIs(hasattr(book, "is_book_alias"), False)