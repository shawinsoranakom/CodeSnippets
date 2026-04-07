def test_distinct_on_aggregate(self):
        for aggregate, expected_result in (
            (Avg, 4.125),
            (Count, 4),
            (Sum, 16.5),
        ):
            with self.subTest(aggregate=aggregate.__name__):
                books = Book.objects.aggregate(
                    ratings=aggregate("rating", distinct=True)
                )
                self.assertEqual(books["ratings"], expected_result)