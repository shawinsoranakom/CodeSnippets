def test_combined_f_expression_annotation_with_aggregation(self):
        book = (
            Book.objects.filter(isbn="159059725")
            .annotate(
                combined=ExpressionWrapper(
                    F("price") * F("pages"), output_field=FloatField()
                ),
                rating_count=Count("rating"),
            )
            .first()
        )
        self.assertEqual(book.combined, 13410.0)
        self.assertEqual(book.rating_count, 1)