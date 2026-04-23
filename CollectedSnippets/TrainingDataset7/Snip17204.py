def test_order_by_aggregate(self):
        authors = (
            Author.objects.values("age")
            .annotate(age_count=Count("age"))
            .order_by("age_count", "age")
        )
        self.assertQuerySetEqual(
            authors,
            [
                (25, 1),
                (34, 1),
                (35, 1),
                (37, 1),
                (45, 1),
                (46, 1),
                (57, 1),
                (29, 2),
            ],
            lambda a: (a["age"], a["age_count"]),
        )