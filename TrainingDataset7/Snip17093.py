def test_exclude_on_aggregate(self):
        # Regression for #10010: exclude on an aggregate field is correctly
        # negated
        self.assertEqual(len(Book.objects.annotate(num_authors=Count("authors"))), 6)
        self.assertEqual(
            len(
                Book.objects.annotate(num_authors=Count("authors")).filter(
                    num_authors__gt=2
                )
            ),
            1,
        )
        self.assertEqual(
            len(
                Book.objects.annotate(num_authors=Count("authors")).exclude(
                    num_authors__gt=2
                )
            ),
            5,
        )

        self.assertEqual(
            len(
                Book.objects.annotate(num_authors=Count("authors"))
                .filter(num_authors__lt=3)
                .exclude(num_authors__lt=2)
            ),
            2,
        )
        self.assertEqual(
            len(
                Book.objects.annotate(num_authors=Count("authors"))
                .exclude(num_authors__lt=2)
                .filter(num_authors__lt=3)
            ),
            2,
        )