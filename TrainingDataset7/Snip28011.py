def test_ordering_grouping_by_key_transform(self):
        base_qs = NullableJSONModel.objects.filter(value__d__0__isnull=False)
        for qs in (
            base_qs.order_by("value__d__0"),
            base_qs.annotate(
                key=KeyTransform("0", KeyTransform("d", "value"))
            ).order_by("key"),
        ):
            self.assertSequenceEqual(qs, [self.objs[4]])
        none_val = "" if connection.features.interprets_empty_strings_as_nulls else None
        qs = NullableJSONModel.objects.filter(value__isnull=False)
        self.assertQuerySetEqual(
            qs.filter(value__isnull=False)
            .annotate(key=KT("value__d__1__f"))
            .values("key")
            .annotate(count=Count("key"))
            .order_by("count"),
            [(none_val, 0), ("g", 1)],
            operator.itemgetter("key", "count"),
        )