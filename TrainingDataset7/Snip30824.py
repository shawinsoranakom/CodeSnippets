def test_null_in_exclude_qs(self):
        none_val = "" if connection.features.interprets_empty_strings_as_nulls else None
        self.assertQuerySetEqual(
            NullableName.objects.exclude(name__in=[]),
            ["i1", none_val],
            attrgetter("name"),
        )
        self.assertQuerySetEqual(
            NullableName.objects.exclude(name__in=["i1"]),
            [none_val],
            attrgetter("name"),
        )
        self.assertQuerySetEqual(
            NullableName.objects.exclude(name__in=["i3"]),
            ["i1", none_val],
            attrgetter("name"),
        )
        inner_qs = NullableName.objects.filter(name="i1").values_list("name")
        self.assertQuerySetEqual(
            NullableName.objects.exclude(name__in=inner_qs),
            [none_val],
            attrgetter("name"),
        )
        # The inner queryset wasn't executed - it should be turned
        # into subquery above
        self.assertIs(inner_qs._result_cache, None)