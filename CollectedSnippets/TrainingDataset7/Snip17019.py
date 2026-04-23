def test_aggregation_default_group_by(self):
        qs = (
            Publisher.objects.values("name")
            .annotate(
                books=Count("book"),
                pages=Sum("book__pages", default=0),
            )
            .filter(books=0)
        )
        self.assertSequenceEqual(
            qs,
            [{"name": "Jonno's House of Books", "books": 0, "pages": 0}],
        )