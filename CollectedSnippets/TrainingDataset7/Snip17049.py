def test_string_agg_filter_in_subquery(self):
        aggregate = StringAgg(
            "authors__name",
            delimiter=Value(";"),
            filter=~Q(authors__name__startswith="J"),
        )
        subquery = (
            Book.objects.filter(
                pk=OuterRef("pk"),
            )
            .annotate(agg=aggregate)
            .values("agg")
        )
        values = list(
            Book.objects.annotate(
                agg=Subquery(subquery),
            ).values_list("agg", flat=True)
        )

        expected_values = [
            "Adrian Holovaty",
            "Brad Dayley",
            "Paul Bissex;Wesley J. Chun",
            "Peter Norvig;Stuart Russell",
            "Peter Norvig",
            "" if connection.features.interprets_empty_strings_as_nulls else None,
        ]

        self.assertQuerySetEqual(expected_values, values, ordered=False)