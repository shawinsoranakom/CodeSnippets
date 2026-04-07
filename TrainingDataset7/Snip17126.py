def test_quoting_aggregate_order_by(self):
        qs = (
            Book.objects.filter(name="Python Web Development with Django")
            .annotate(authorCount=Count("authors"))
            .order_by("authorCount")
        )
        self.assertQuerySetEqual(
            qs,
            [
                ("Python Web Development with Django", 3),
            ],
            lambda b: (b.name, b.authorCount),
        )