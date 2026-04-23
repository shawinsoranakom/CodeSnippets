def test_aggregate_and_annotate_duplicate_columns(self):
        books = (
            Book.objects.values("isbn")
            .annotate(
                name=F("publisher__name"),
                num_authors=Count("authors"),
            )
            .order_by("isbn")
        )
        self.assertSequenceEqual(
            books,
            [
                {"isbn": "013235613", "name": "Prentice Hall", "num_authors": 3},
                {"isbn": "013790395", "name": "Prentice Hall", "num_authors": 2},
                {"isbn": "067232959", "name": "Sams", "num_authors": 1},
                {"isbn": "155860191", "name": "Morgan Kaufmann", "num_authors": 1},
                {"isbn": "159059725", "name": "Apress", "num_authors": 2},
                {"isbn": "159059996", "name": "Apress", "num_authors": 1},
            ],
        )