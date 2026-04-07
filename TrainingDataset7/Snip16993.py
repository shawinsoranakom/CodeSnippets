def test_aggregation_subquery_annotation_values(self):
        """
        Subquery annotations and external aliases are excluded from the GROUP
        BY if they are not selected.
        """
        books_qs = (
            Book.objects.annotate(
                first_author_the_same_age=Subquery(
                    Author.objects.filter(
                        age=OuterRef("contact__friends__age"),
                    )
                    .order_by("age")
                    .values("id")[:1],
                )
            )
            .filter(
                publisher=self.p1,
                first_author_the_same_age__isnull=False,
            )
            .annotate(
                min_age=Min("contact__friends__age"),
            )
            .values("name", "min_age")
            .order_by("name")
        )
        self.assertEqual(
            list(books_qs),
            [
                {"name": "Practical Django Projects", "min_age": 34},
                {
                    "name": (
                        "The Definitive Guide to Django: Web Development Done Right"
                    ),
                    "min_age": 29,
                },
            ],
        )