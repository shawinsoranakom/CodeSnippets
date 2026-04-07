def test_empty(self):
        # Regression for #10089: Check handling of empty result sets with
        # aggregates
        self.assertEqual(Book.objects.filter(id__in=[]).count(), 0)

        vals = Book.objects.filter(id__in=[]).aggregate(
            num_authors=Count("authors"),
            avg_authors=Avg("authors"),
            max_authors=Max("authors"),
            max_price=Max("price"),
            max_rating=Max("rating"),
        )
        self.assertEqual(
            vals,
            {
                "max_authors": None,
                "max_rating": None,
                "num_authors": 0,
                "avg_authors": None,
                "max_price": None,
            },
        )

        qs = (
            Publisher.objects.filter(name="Jonno's House of Books")
            .annotate(
                num_authors=Count("book__authors"),
                avg_authors=Avg("book__authors"),
                max_authors=Max("book__authors"),
                max_price=Max("book__price"),
                max_rating=Max("book__rating"),
            )
            .values()
        )
        self.assertSequenceEqual(
            qs,
            [
                {
                    "max_authors": None,
                    "name": "Jonno's House of Books",
                    "num_awards": 0,
                    "max_price": None,
                    "num_authors": 0,
                    "max_rating": None,
                    "id": self.p5.id,
                    "avg_authors": None,
                }
            ],
        )