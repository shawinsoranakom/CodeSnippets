def test_decimal_aggregate_annotation_filter(self):
        """
        Filtering on an aggregate annotation with Decimal values should work.
        Requires special handling on SQLite (#18247).
        """
        self.assertEqual(
            len(
                Author.objects.annotate(sum=Sum("book_contact_set__price")).filter(
                    sum__gt=Decimal(40)
                )
            ),
            1,
        )
        self.assertEqual(
            len(
                Author.objects.annotate(sum=Sum("book_contact_set__price")).filter(
                    sum__lte=Decimal(40)
                )
            ),
            4,
        )