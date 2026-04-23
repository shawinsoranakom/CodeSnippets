def test_string_agg_filter_outerref(self):
        values = (
            Publisher.objects.annotate(
                stringagg=Subquery(
                    Book.objects.annotate(
                        stringagg=StringAgg(
                            "name",
                            delimiter=Value(";"),
                            order_by=OuterRef("num_awards"),
                        )
                    ).values("stringagg")[:1]
                )
            )
            .values("stringagg")
            .order_by("id")
        )

        self.assertQuerySetEqual(
            values,
            [
                {
                    "stringagg": "The Definitive Guide to Django: "
                    "Web Development Done Right"
                }
            ]
            * 5,
        )