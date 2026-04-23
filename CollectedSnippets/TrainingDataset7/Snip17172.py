def test_full_expression_annotation(self):
        books = Book.objects.annotate(
            selected=ExpressionWrapper(~Q(pk__in=[]), output_field=BooleanField()),
        )
        self.assertEqual(len(books), Book.objects.count())
        self.assertTrue(all(book.selected for book in books))