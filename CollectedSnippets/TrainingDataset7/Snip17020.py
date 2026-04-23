def test_aggregation_default_compound_expression(self):
        # Scale rating to a percentage; default to 50% if no books published.
        formula = Avg("book__rating", default=2.5) * 20.0
        queryset = Publisher.objects.annotate(rating=formula).order_by("name")
        self.assertSequenceEqual(
            queryset.values("name", "rating"),
            [
                {"name": "Apress", "rating": 85.0},
                {"name": "Jonno's House of Books", "rating": 50.0},
                {"name": "Morgan Kaufmann", "rating": 100.0},
                {"name": "Prentice Hall", "rating": 80.0},
                {"name": "Sams", "rating": 60.0},
            ],
        )