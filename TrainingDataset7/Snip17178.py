def test_combined_expression_annotation_with_aggregation(self):
        book = Book.objects.annotate(
            combined=ExpressionWrapper(
                Value(3) * Value(4), output_field=IntegerField()
            ),
            rating_count=Count("rating"),
        ).first()
        self.assertEqual(book.combined, 12)
        self.assertEqual(book.rating_count, 1)