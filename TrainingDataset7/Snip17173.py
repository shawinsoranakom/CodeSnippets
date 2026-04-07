def test_full_expression_wrapped_annotation(self):
        books = Book.objects.annotate(
            selected=Coalesce(~Q(pk__in=[]), True),
        )
        self.assertEqual(len(books), Book.objects.count())
        self.assertTrue(all(book.selected for book in books))