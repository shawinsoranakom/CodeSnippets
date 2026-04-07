def test_q_expression_annotation_with_aggregation(self):
        book = (
            Book.objects.filter(isbn="159059725")
            .annotate(
                isnull_pubdate=ExpressionWrapper(
                    Q(pubdate__isnull=True),
                    output_field=BooleanField(),
                ),
                rating_count=Count("rating"),
            )
            .first()
        )
        self.assertIs(book.isnull_pubdate, False)
        self.assertEqual(book.rating_count, 1)