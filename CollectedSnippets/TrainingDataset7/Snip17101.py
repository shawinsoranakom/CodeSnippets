def test_aggregate_subquery_annotation(self):
        # Regression for #10182 - Queries with aggregate calls are correctly
        # realiased when used in a subquery
        ids = (
            Book.objects.filter(pages__gt=100)
            .annotate(n_authors=Count("authors"))
            .filter(n_authors__gt=2)
            .order_by("n_authors")
        )
        self.assertQuerySetEqual(
            Book.objects.filter(id__in=ids),
            [
                "Python Web Development with Django",
            ],
            lambda b: b.name,
        )