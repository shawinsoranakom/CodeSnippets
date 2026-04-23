def test_stddev(self):
        self.assertEqual(
            Book.objects.aggregate(StdDev("pages")),
            {"pages__stddev": Approximate(311.46, 1)},
        )

        self.assertEqual(
            Book.objects.aggregate(StdDev("rating")),
            {"rating__stddev": Approximate(0.60, 1)},
        )

        self.assertEqual(
            Book.objects.aggregate(StdDev("price")),
            {"price__stddev": Approximate(Decimal("24.16"), 2)},
        )

        self.assertEqual(
            Book.objects.aggregate(StdDev("pages", sample=True)),
            {"pages__stddev": Approximate(341.19, 2)},
        )

        self.assertEqual(
            Book.objects.aggregate(StdDev("rating", sample=True)),
            {"rating__stddev": Approximate(0.66, 2)},
        )

        self.assertEqual(
            Book.objects.aggregate(StdDev("price", sample=True)),
            {"price__stddev": Approximate(Decimal("26.46"), 1)},
        )

        self.assertEqual(
            Book.objects.aggregate(Variance("pages")),
            {"pages__variance": Approximate(97010.80, 1)},
        )

        self.assertEqual(
            Book.objects.aggregate(Variance("rating")),
            {"rating__variance": Approximate(0.36, 1)},
        )

        self.assertEqual(
            Book.objects.aggregate(Variance("price")),
            {"price__variance": Approximate(Decimal("583.77"), 1)},
        )

        self.assertEqual(
            Book.objects.aggregate(Variance("pages", sample=True)),
            {"pages__variance": Approximate(116412.96, 1)},
        )

        self.assertEqual(
            Book.objects.aggregate(Variance("rating", sample=True)),
            {"rating__variance": Approximate(0.44, 2)},
        )

        self.assertEqual(
            Book.objects.aggregate(Variance("price", sample=True)),
            {"price__variance": Approximate(Decimal("700.53"), 2)},
        )