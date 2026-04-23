def test_ordering_grouping_by_count(self):
        qs = (
            NullableJSONModel.objects.filter(
                value__isnull=False,
            )
            .values("value__d__0")
            .annotate(count=Count("value__d__0"))
            .order_by("count")
        )
        self.assertQuerySetEqual(qs, [0, 1], operator.itemgetter("count"))