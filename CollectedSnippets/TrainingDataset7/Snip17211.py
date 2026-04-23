def test_boolean_value_annotation(self):
        books = Book.objects.annotate(
            is_book=Value(True, output_field=BooleanField()),
            is_pony=Value(False, output_field=BooleanField()),
            is_none=Value(None, output_field=BooleanField(null=True)),
        )
        self.assertGreater(len(books), 0)
        for book in books:
            self.assertIs(book.is_book, True)
            self.assertIs(book.is_pony, False)
            self.assertIsNone(book.is_none)