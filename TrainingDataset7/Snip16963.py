def test_annotate_values_list(self):
        books = (
            Book.objects.filter(pk=self.b1.pk)
            .annotate(mean_age=Avg("authors__age"))
            .values_list("pk", "isbn", "mean_age")
        )
        self.assertEqual(list(books), [(self.b1.id, "159059725", 34.5)])

        books = (
            Book.objects.filter(pk=self.b1.pk)
            .annotate(mean_age=Avg("authors__age"))
            .values_list("isbn")
        )
        self.assertEqual(list(books), [("159059725",)])

        books = (
            Book.objects.filter(pk=self.b1.pk)
            .annotate(mean_age=Avg("authors__age"))
            .values_list("mean_age")
        )
        self.assertEqual(list(books), [(34.5,)])

        books = (
            Book.objects.filter(pk=self.b1.pk)
            .annotate(mean_age=Avg("authors__age"))
            .values_list("mean_age", flat=True)
        )
        self.assertEqual(list(books), [34.5])

        books = (
            Book.objects.values_list("price")
            .annotate(count=Count("price"))
            .order_by("-count", "price")
        )
        self.assertEqual(
            list(books),
            [
                (Decimal("29.69"), 2),
                (Decimal("23.09"), 1),
                (Decimal("30"), 1),
                (Decimal("75"), 1),
                (Decimal("82.8"), 1),
            ],
        )